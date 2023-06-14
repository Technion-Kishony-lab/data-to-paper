from examples.run_project import get_paper

goal = "Find prevalence and predictors of stroke among individuals with prediabetes and diabetes" \
       "in Florida. Test the hypothesis that demographic factors like age and race and risk factors like " \
        "smoking, obesity, hypertension and hypercholesterolemia are associated with stroke"

RUN_PARAMETERS = dict(
    project='brfss_florida',
    data_filenames=["brfss_2019_florida.csv"],
    research_goal=None,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    get_paper(**RUN_PARAMETERS,
              output_folder='possible_paper_1',
              should_mock_servers=True,
              save_on_repo=True)
