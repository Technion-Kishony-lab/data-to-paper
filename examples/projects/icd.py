from examples.run_project import get_paper

get_paper(project='icd',
          data_filenames=['PATIENTS.csv', 'DIAGNOSES_ICD.csv'],
          research_goal=None,
          output_folder='out1',
          should_do_data_exploration=True,
          should_mock_servers=True)
