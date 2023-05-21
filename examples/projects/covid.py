from examples.run_project import get_paper

get_paper(project='covid',
          data_filenames=["eng_covid_vaccine_side_effects.csv"],
          research_goal=None,
          output_folder='out1',
          should_do_data_exploration=True,
          should_mock_servers=True)
