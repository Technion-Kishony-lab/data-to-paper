from examples.run_project import get_paper

RUN_PARAMETERS = dict(
    project='covid',
    data_filenames=["eng_covid_vaccine_side_effects.csv"],
    research_goal=None,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    get_paper(**RUN_PARAMETERS,
              output_folder='out1',
              should_mock_servers=True)
