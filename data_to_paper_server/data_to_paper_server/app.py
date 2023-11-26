import gevent
from gevent import monkey
monkey.patch_all()
import json
import os
import uuid
from pathlib import Path
from queue import Empty
from typing import Optional

from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, join_room

from data_to_paper_examples.examples import run_project, projects
from data_to_paper_examples.examples.run_project import get_file_descriptions, copy_datafiles_to_data_folder, get_output_path
from data_to_paper.base_products import DataFileDescriptions, DataFileDescription

from data_to_paper.researches_types.scientific_research.cast import ScientificAgent
from data_to_paper.researches_types.scientific_research.run_steps import ScientificStepsRunner
from data_to_paper_server.consts import BASE_DIRECTORY
from data_to_paper_server.serializers import SerializedAction
from data_to_paper_server.websocket_messenger import QueueMessenger
import gipc

"""
SET RUN PARAMETERS HERE
"""
PROJECT: Optional[str] = 'meconium'  # None to get from web ui

if PROJECT:
    load_from_repo = True  # False to load from local examples folder (outside the repo)

    # Choose RUN_PARAMETERS. `None` to get from web ui, or set to an example project
    RUN_PARAMETERS = getattr(projects, PROJECT).RUN_PARAMETERS

    # Choose TEMP_FOLDER_TO_RUN_IN.
    # `None` for /tmp/data_to_paper_server/ + id, or set to the local examples temp folder:
    INPUT_DIRECTORY = run_project.get_input_path(PROJECT, load_from_repo)
    TEMP_FOLDER_TO_RUN_IN: Optional[str] = INPUT_DIRECTORY / 'temp_folder'

    # Choose OUTPUT_DIRECTORY. `None` for TEMP_FOLDER_TO_RUN_IN/output, or set to the local examples output folder:
    OUTPUT_DIRECTORY: Optional[Path] = get_output_path(PROJECT,
                                                       'client_example', save_on_repo=True)

    # Choose MOCK_SERVERS.
    # `False` to avoid mocking servers
    # `True` to mock and save responses to OUTPUT_DIRECTORY.
    # Or set to a local path.
    MOCK_SERVERS = True
else:
    RUN_PARAMETERS = None
    TEMP_FOLDER_TO_RUN_IN: Optional[str] = None
    INPUT_DIRECTORY: Optional[Path] = None
    OUTPUT_DIRECTORY: Optional[Path] = None
    MOCK_SERVERS = True


app = Flask(__name__, static_folder='build')
app.config['SECRET_KEY'] = 'my first ever ⁄!#P@EL!'

socketio = SocketIO(app, async_mode='gevent')


THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


PROCESSES = []

PAPER_IDS_TO_SERIALIZED_ACTIONS = {}


def _run(
        id_,
        writer,
        step_runner_kwargs,
):
    os.environ['CLIENT_SERVER_MODE'] = 'True'
    QueueMessenger(first_person=ScientificAgent.Performer, writer=writer)
    ScientificStepsRunner(**step_runner_kwargs).run_all_steps()
    # TODO: this is a hack to make sure the last action is sent- once the writer dies, gipc's reader can't read
    gevent.sleep(10)


def run_scientist_gpt_in_separate_process(id_, step_runner_kwargs):
    reader, writer = gipc.pipe()
    process = gipc.start_process(
        _run,
        args=(id_, writer, step_runner_kwargs),
    )
    PROCESSES.append(process)

    while True:
        if not process.is_alive():
            break
        try:
            serialized = reader.get()
        except Empty:
            continue
        except EOFError:
            break

        if serialized is not None:
            PAPER_IDS_TO_SERIALIZED_ACTIONS.setdefault(id_, []).append(serialized)
            socketio.emit(
                serialized.event,
                {
                    'eventId': len(PAPER_IDS_TO_SERIALIZED_ACTIONS[id_]),
                    'data': serialized.data
                },
                to=id_
            )


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/hello')
def hello_world():
    return 'Hello, World!'


@app.route('/papers/<id_>/products/<name>')
def get_product(id_, name):
    output_directory = BASE_DIRECTORY / id_ / 'output'
    return send_from_directory(output_directory, name, as_attachment=True)


@app.route('/api/papers', methods=['POST'])
def create_paper():
    id_ = str(uuid.uuid4())

    if TEMP_FOLDER_TO_RUN_IN is None:
        paper_path = BASE_DIRECTORY / id_
    else:
        paper_path = Path(TEMP_FOLDER_TO_RUN_IN)
    if not paper_path.exists():
        paper_path.mkdir()

    if OUTPUT_DIRECTORY is None:
        output_directory = paper_path / 'output'
        output_directory.mkdir()
    else:
        output_directory = Path(OUTPUT_DIRECTORY)

    if RUN_PARAMETERS is None:  # real run - get from web ui
        data_file_descriptions = DataFileDescriptions(data_folder=paper_path)
        for (f, description) in zip(request.files.getlist('file'), request.form.getlist('description')):
            path = paper_path / f.filename
            f.save(path)
            data_file_descriptions.append(
                DataFileDescription(
                    file_path=f.filename,
                    description=description
                )
            )
        step_runner_kwargs = dict(
            data_file_descriptions=data_file_descriptions,
            research_goal=request.form['goal'] or None,
            should_do_data_exploration=True,  # TODO: get from web ui
            output_directory=output_directory,
            mock_servers=MOCK_SERVERS,
        )
    else:  # run from demo
        copy_datafiles_to_data_folder(data_filenames=RUN_PARAMETERS['data_filenames'],
                                      input_path=INPUT_DIRECTORY,
                                      data_folder=paper_path)
        step_runner_kwargs = dict(
            data_file_descriptions=get_file_descriptions(input_directory=INPUT_DIRECTORY,
                                                         data_filenames=RUN_PARAMETERS['data_filenames'],
                                                         data_folder=paper_path),
            research_goal=RUN_PARAMETERS['research_goal'],
            should_do_data_exploration=RUN_PARAMETERS['should_do_data_exploration'],
            output_directory=output_directory,
            mock_servers=MOCK_SERVERS,
        )

    socketio.start_background_task(target=run_scientist_gpt_in_separate_process, id_=id_,
                                   step_runner_kwargs=step_runner_kwargs)
    return json.dumps(
        {
            'id': id_
        }
    )


@app.route('/api/papers/<paper_id>', methods=['GET'])
def get_paper(paper_id):
    actions = PAPER_IDS_TO_SERIALIZED_ACTIONS.get(paper_id, [])
    # TODO: shouldn't be looking at strings
    conversations = [{
        'eventId': i,
        'data': action.data
    } for i, action in enumerate(actions) if action.event == 'CreateConversation']
    messages = [
        {
            'eventId': i,
            'data': action.data
        } for i, action in enumerate(actions) if action.event == 'AppendMessage'
    ]
    products = [
        {
            'eventId': i,
            'data': action.data
        } for i, action in enumerate(actions) if action.event == 'Output'
    ]
    stages = [
        {
            'eventId': i,
            'data': action.data
        } for i, action in enumerate(actions) if action.event == 'AdvanceStage'
    ]
    return json.dumps({
        'conversations': conversations,
        'messages': messages,
        'products': products,
        'stages': stages
    })


@socketio.on('join_paper')
def join_paper(data):
    join_room(data['id'])


@socketio.on('connect')
def test_connect(auth):
    print('connected')


if __name__ == '__main__':
    try:
        socketio.run(app, port=os.getenv('PORT', 8000), host='0.0.0.0')
    finally:
        for p in PROCESSES:
            if p.is_alive():
                p.terminate()
