import sys
from functools import partial

from data_to_paper.env import CHOSEN_APP
from data_to_paper.interactive.get_app import get_or_create_app
from data_to_paper_examples.examples.run_project import get_paper

goal = "Using machine learning models and multivariate analysis find risk factors for diabetes. " \
       "Build predictive models to predict diabetes from health indicators.",

project_specific_goal_guidelines = """\
* Avoid goals and hypotheses that involve ethic issues like sociodemographic (Income, Education, etc.) \
and psychological (Mental Health) variables. 
Note though that you can, and should, still use these as confounding variables if needed.
"""

RUN_PARAMETERS = dict(
    project='diabetes',
    data_filenames=["diabetes_binary_health_indicators_BRFSS2015.csv"],
    research_goal=None,
    should_do_data_exploration=True,
    should_mock_servers=True,
    load_from_repo=True,
    save_on_repo=True,
    project_specific_goal_guidelines=project_specific_goal_guidelines,
    output_folder='run011'
)

if __name__ == '__main__':
    if CHOSEN_APP != 'pyside':
        get_paper(**RUN_PARAMETERS)
    else:
        app = get_or_create_app()
        app.start_worker(partial(get_paper, **RUN_PARAMETERS))
        sys.exit(app.q_application.exec())
