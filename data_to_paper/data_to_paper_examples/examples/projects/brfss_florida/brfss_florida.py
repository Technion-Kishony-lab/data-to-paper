from data_to_paper_examples.examples.run_project import get_paper

goal = "GOAL:\n" \
       "Find prevalence and predictors of stroke among individuals with Prediabetes and Diabetes in Florida.\n" \
       "HYPOTHESES:\n" \
       "1. Prevalence of stroke among individuals with Prediabetes is higher than among individual without it.\n" \
       "2. Prevalence of stroke among individuals with Diabetes is higher than among individual without it.\n" \
       "3. The odds ratio of Stroke among individuals with Prediabetes is higher for individuals from different " \
       "demographic backgrounds (Age, Sex, Race).\n" \
       "4. The odds ratio of Stroke among individuals with Diabetes is higher for individuals from different" \
       "demographic backgrounds (Age, Sex, Race).\n" \
       "5. The association between Diabetes and Stroke differs by factors like Hypertension, " \
       "Hypercholesterolemia and Depression, when adjusting for demographic factors.\n" \
       "6. The association between Prediabetes and Stroke differs by factors like Hypertension, " \
       "Hypercholesterolemia and Depression, when adjusting for demographic factors."

RUN_PARAMETERS = dict(
    project='brfss_florida',
    data_filenames=["brfss_2019_florida.csv"],
    research_goal=goal,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    get_paper(**RUN_PARAMETERS,
              output_folder='possible_paper_1',
              should_mock_servers=True,
              save_on_repo=True)
