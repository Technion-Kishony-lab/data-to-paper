from data_to_paper_examples.examples.run_project import get_paper

goal = """
## Research Goal:

To construct and test \
2 different formula-based models \
for the optimal tracheal tube depth \
(defined here as `OTTD`, not an official term). 

### FORMULA-BASED MODELS:
Your analysis code should compute the following 2 formula-based models for the OTTD:

- Height Formula-based Model:
OTTD = height [cm] / 10 + 5 cm 
- Age Formula-based Model:
optimal tube depth is provided for each age group:
0 <= age [years] < 0.5: OTTD = 9 cm
0.5 <= age [years] < 1: OTTD = 10 cm
1 < age [years] < 2: OTTD = 11 cm
2 < age [years]: OTTD = 12 cm + (age [years]) * 0.5 cm / year

## Hypothesis:

- The two formula-based models will significantly differ in their predictive power \
(as measured by their squared residuals on the same test set). 

"""


NAME_OF_REPRODUCED_PAPER = 'Machine learning model for predicting the optimal depth of tracheal tube insertion ' \
                           'in pediatric patients: A retrospective cohort study'

RUN_PARAMETERS = dict(
    project="t_tube_insertion",
    data_filenames=["tracheal_tube_insertion.csv"],
    research_goal=goal,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    for run_name in [f'easier20{i}' for i in range(1, 10)] + ['easier210']:
        get_paper(**RUN_PARAMETERS,
                  output_folder=run_name,
                  should_mock_servers=True,
                  excluded_citation_titles=[NAME_OF_REPRODUCED_PAPER],
                  load_from_repo=True,
                  save_on_repo=True)
