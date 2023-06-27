from examples.run_project import get_paper

goal = "Using machine learning models and multivariate analysis find risk factors for diabetes. " \
       "Build predictive models to predict diabetes from health indicators.",

RUN_PARAMETERS = dict(
    project='diabetes',
    data_filenames=["diabetes_binary_health_indicators_BRFSS2015.csv"],
    research_goal=None,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    get_paper(**RUN_PARAMETERS,
              output_folder='tweeter_5',
              should_mock_servers=True,
              load_from_repo=True,
              save_on_repo=True)
