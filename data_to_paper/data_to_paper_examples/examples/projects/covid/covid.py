import sys
from functools import partial

from data_to_paper.env import CHOSEN_APP
from data_to_paper.interactive.get_app import create_app
from data_to_paper_examples.examples.run_project import get_paper

RUN_PARAMETERS = dict(
    project='covid',
    data_filenames=["eng_covid_vaccine_side_effects.csv"],
    research_goal=None,
    should_do_data_exploration=True,
    output_folder='out1',
    should_mock_servers=True,
    save_on_repo=True,
)

if __name__ == '__main__':
    if CHOSEN_APP != 'pyside':
        get_paper(**RUN_PARAMETERS)
    else:
        app = create_app()
        app.start_worker(partial(get_paper, **RUN_PARAMETERS))
        sys.exit(app.q_application.exec())
