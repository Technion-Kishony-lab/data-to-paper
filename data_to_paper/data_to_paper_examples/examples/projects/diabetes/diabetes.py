import os

from data_to_paper_examples.examples.run_project import get_paper

os.environ['DATA_EXPLORATION_MODEL_ENGINE'] = 'CODELLAMA'

goal = "Using machine learning models and multivariate analysis find risk factors for diabetes. " \
       "Build predictive models to predict diabetes from health indicators.",

RUN_PARAMETERS = dict(
    project='diabetes',
    data_filenames=["diabetes_binary_health_indicators_BRFSS2015.csv"],
    research_goal=None,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    for model_engine in ["CODELLAMA", "GPT4", "GPT35_TURBO", "LLAMA_2_7b", "LLAMA_2_70b"]:
        os.environ['DATA_EXPLORATION_MODEL_ENGINE'] = model_engine
        for run_name in ['{}_run_{:01d}'.format(model_engine, i) for i in range(1, 11)]:
            get_paper(**RUN_PARAMETERS,
                      output_folder=run_name,
                      should_mock_servers=True,
                      load_from_repo=True,
                      save_on_repo=True)
