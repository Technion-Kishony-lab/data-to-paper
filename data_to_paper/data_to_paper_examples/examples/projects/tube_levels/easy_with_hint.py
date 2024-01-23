from data_to_paper_examples.examples.run_project import get_paper

goal = """
## Research Goal:

To construct and test \
2 different machine-learning models \
for the optimal tracheal tube depth \
(defined here as `OTTD`, not an official term). 

### ML MODELS:
Using the provided features (age, sex, height, weight), your analysis code should create \
and evaluate the following 2 machine learning models for predicting the OTTD:

- Random Forest (RF)
- Elastic Net (EN)

Important: It is necessary to hyper-parameter tune each of the models.

## Hypothesis:

- The two machine-learning models will significantly differ in their predictive power \
(as measured by their squared residuals (prediction - target)**2 on the same test set). 

"""


NAME_OF_REPRODUCED_PAPER = 'Machine learning model for predicting the optimal depth of tracheal tube insertion ' \
                           'in pediatric patients: A retrospective cohort study'

RUN_PARAMETERS = dict(
    project="tube_levels",
    data_filenames=["tracheal_tube_insertion.csv"],
    research_goal=goal,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    for run_name in ['easy_with_hint2{:02d}'.format(i) for i in range(1, 11)]:
        get_paper(**RUN_PARAMETERS,
                  output_folder=run_name,
                  should_mock_servers=True,
                  excluded_citation_titles=[NAME_OF_REPRODUCED_PAPER],
                  load_from_repo=True,
                  save_on_repo=True)
