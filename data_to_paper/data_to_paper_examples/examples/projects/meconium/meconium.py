import sys
from functools import partial

from data_to_paper.env import CHOSEN_APP
from data_to_paper.interactive.get_app import create_app
from data_to_paper_examples.examples.run_project import get_paper

goal = """
Research goal: 
Examining the impact of guideline change on neonatal treatment and outcomes.

Hypothesis:
- Change in treatment policy lead to change in treatments.
- The change in treatment policy improved neonatal outcome, measured by duration of stay, apgar scores, etc.
"""

RUN_PARAMETERS = dict(
    project='meconium',
    data_filenames=["meconium_nicu_dataset_preprocessed_short.csv"],
    research_goal=goal,
    should_do_data_exploration=True,
    output_folder='paper01',
    should_mock_servers=True,
    load_from_repo=True,
    save_on_repo=True,
)

if __name__ == '__main__':
    if CHOSEN_APP != 'pyside':
        get_paper(**RUN_PARAMETERS)
    else:
        app = create_app()
        app.start_worker(partial(get_paper, **RUN_PARAMETERS))
        sys.exit(app.q_application.exec())
