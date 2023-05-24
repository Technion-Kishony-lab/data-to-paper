from examples.run_project import get_paper

get_paper(project='diabetes',
          data_filenames=["diabetes_binary_health_indicators_BRFSS2015.csv"],
          research_goal="Using machine learning models and multivariate analysis find risk factors for diabetes. "\
                        "Build predictive models to predict diabetes from health indicators.",
          output_folder='out4',
          should_do_data_exploration=True,
          should_mock_servers=True)
