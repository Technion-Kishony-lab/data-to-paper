from examples.run_project import get_paper

RUN_PARAMETERS = dict(
    project='icd',
    data_filenames=['PATIENTS.csv', 'DIAGNOSES_ICD.csv'],
    research_goal=None,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    get_paper(**RUN_PARAMETERS,
              output_folder='out1',
              should_mock_servers=True)
