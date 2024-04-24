import sys
from functools import partial

from data_to_paper.env import CHOSEN_APP
from data_to_paper.interactive.get_app import get_or_create_app
from data_to_paper_examples.examples.run_project import get_paper

goal = """
## Research Goal:

To construct and test \
4 different machine-learning models and 3 different formula-based models \
for the optimal tracheal tube depth \
(defined here as `OTTD`, not an official term). 

### ML MODELS:
Using the provided features (age, sex, height, weight), your analysis code should create \
and evaluate the following 4 machine learning models for predicting the OTTD:

- Random Forest (RF)
- Elastic Net (EN)
- Support Vector Machine (SVM)
- Neural Network (NN)

Important: It is necessary to hyper-parameter tune each of the models.

### FORMULA-BASED MODELS:
Your analysis code should compute the following 3 formula-based models for the OTTD:

- Height Formula-based Model: 
OTTD = height [cm] / 10 + 5 cm 

- Age Formula-based Model:
optimal tube depth is provided for each age group:
0 <= age [years] < 0.5: OTTD = 9 cm 
0.5 <= age [years] < 1: OTTD = 10 cm 
1 < age [years] < 2: OTTD = 11 cm 
2 < age [years]: OTTD = 12 cm + (age [years]) * 0.5 cm / year  

- ID Formula-based Model:
OTTD (in cm) = 3 * (tube ID [mm]) * cm/mm


## Hypotheses:

- Each of the 4 machine learning models will have significantly better predictive power than each of the formula-based \
models \
(as measured by their squared residuals (prediction - target)**2 on the same test set). 

"""


NAME_OF_REPRODUCED_PAPER = 'Machine learning model for predicting the optimal depth of tracheal tube insertion ' \
                           'in pediatric patients: A retrospective cohort study'


RUN_PARAMETERS = dict(
    project='t_tube_insertion',
    data_filenames=["tracheal_tube_insertion.csv"],
    research_goal=goal,
    excluded_citation_titles=[NAME_OF_REPRODUCED_PAPER],
    output_folder='run004'
)

if __name__ == '__main__':
    if CHOSEN_APP != 'pyside':
        get_paper(**RUN_PARAMETERS)
    else:
        app = get_or_create_app()
        app.start_worker(partial(get_paper, **RUN_PARAMETERS))
        sys.exit(app.q_application.exec())
