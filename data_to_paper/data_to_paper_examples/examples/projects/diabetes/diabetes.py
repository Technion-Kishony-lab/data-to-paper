import sys
from functools import partial

from data_to_paper.env import CHOSEN_APP
from data_to_paper.interactive import the_app, q_application
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
)

if __name__ == '__main__':
    if CHOSEN_APP != 'pyside':
        get_paper(**RUN_PARAMETERS,
                  output_folder='test_001',
                  project_specific_goal_guidelines=project_specific_goal_guidelines,
                  should_mock_servers=True,
                  load_from_repo=True,
                  save_on_repo=True)
    else:
        the_app.start_worker(partial(get_paper, **RUN_PARAMETERS, output_folder='test_001',
                                     project_specific_goal_guidelines=project_specific_goal_guidelines,
                                     should_mock_servers=True, load_from_repo=True, save_on_repo=True))
        sys.exit(q_application.exec())
