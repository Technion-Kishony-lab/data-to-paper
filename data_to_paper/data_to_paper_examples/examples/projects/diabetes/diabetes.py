from data_to_paper_examples.examples.run_project import get_paper

goal = "Using machine learning models and multivariate analysis find risk factors for diabetes. " \
       "Build predictive models to predict diabetes from health indicators.",

RUN_PARAMETERS = dict(
    project='diabetes',
    data_filenames=["diabetes_binary_health_indicators_BRFSS2015.csv"],
    research_goal=None,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    for run_name in ['paper1301', 'paper1302', 'paper1303', 'paper1304', 'paper1308']:
        get_paper(**RUN_PARAMETERS,
                  output_folder=run_name,
                  should_mock_servers=True,
                  load_from_repo=True,
                  save_on_repo=True)
