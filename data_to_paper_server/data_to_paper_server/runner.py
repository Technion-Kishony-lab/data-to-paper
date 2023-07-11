from data_to_paper.researches_types.scientific_research.cast import ScientificAgent
from data_to_paper.researches_types.scientific_research.run_steps import ScientificStepsRunner
from data_to_paper_server.consts import BASE_DIRECTORY
from data_to_paper_server.websocket_messenger import QueueMessenger


def run_scientist_gpt_with_output_serialization(
        id_,
        goal,
        data_file_descriptions,
        queue
):
    output_directory = BASE_DIRECTORY / id_ / 'output'
    output_directory.mkdir()

    QueueMessenger(first_person=ScientificAgent.Performer, queue=queue)

    ScientificStepsRunner(
        data_file_descriptions=data_file_descriptions,
        research_goal=goal,
        output_directory=output_directory,
        mock_servers=False
    ).run_all_steps()
