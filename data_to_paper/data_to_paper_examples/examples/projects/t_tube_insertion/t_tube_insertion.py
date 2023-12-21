from data_to_paper_examples.examples.run_project import get_paper

goal = """
** Research Goal:

To construct and test 4 different machine-learning models and 3 different formula-based predictions \
for the optimal tracheal tube depth (defined here as `OTTD`, not an official term). 

- ML PREDICTIONS:
Using the provided features (age, sex, height, weight), your analysis code should create, hyperparameter optimize, \
and evaluate the following 4 machine-learning models for predicting the OTTD:

(a) Random forest (RF)
(b) Elastic net (EN)
(c) Support Vector Machine (SVM)
(d) Neural network (NN)

Important: for each of these models, you should split the data to train and test and perform hyperparameter tuning \
using cross-validation. 


- FORMULA-BASED PREDICTIONS:
Your analysis code should compute the following 3 formula-based predictions for the OTTD:

(a) Height-based Method: 
OTTD = height [cm] / 10 + 5 cm 

(b) Age-based Method:
optimal tube depth is provided for each age group:
0 <= age [years] < 0.5: OTTD = 9 cm 
0.5 <= age [years] < 1: OTTD = 10 cm 
1 < age [years] < 2: OTTD = 11 cm 
2 < age [years]: OTTD = 12 cm + (age [years]) * 0.5 cm / year  

(c) ID-based method:
OTTD (in cm) = 3 * (tube ID [mm]) * cm/mm


** Hypotheses:

- Compared across cross-validation folds, the ML models will vary in their performance for predicting the OTTD. 

- Compared across cross-validation folds, each of the 4 optimized ML models will perform better than each of the \
formula-based methods. 
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
    get_paper(**RUN_PARAMETERS,
              output_folder="paper901",
              should_mock_servers=True,
              excluded_citation_titles=[NAME_OF_REPRODUCED_PAPER],
              load_from_repo=True,
              save_on_repo=True)
