from examples.run_project import get_paper

RUN_PARAMETERS = dict(
    project='diabetes',
    data_filenames=["diabetes_binary_health_indicators_BRFSS2015.csv"],
    research_goal="Using machine learning models and multivariate analysis find risk factors for diabetes. "
                  "Build predictive models to predict diabetes from health indicators.",
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    get_paper(**RUN_PARAMETERS,
              output_folder='out4',
              should_mock_servers=True)
