from examples.run_project import get_paper

get_paper(project='diabetes',
          data_filenames=["diabetes_binary_health_indicators_BRFSS2015.csv"],
          research_goal=None,
          output_folder='out1',
          should_do_data_exploration=True,
          should_mock_servers=True)
