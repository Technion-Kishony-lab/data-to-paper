import argparse
import os

from data_to_paper_examples.examples.run_project import get_paper

# Define the command line argument parser
parser = argparse.ArgumentParser(description="Run Diabetes paper generation")

# Add arguments for output_folder and DATA_EXPLORATION_MODEL_ENGINE
parser.add_argument('--output_folder', type=str, default='default_output', help='Output folder for the paper')
parser.add_argument('--model_engine', type=str, default='GPT4', help='GPT model engine to use')

# Parse arguments from the command line
args = parser.parse_args()

# Set the variables from command line arguments
os.environ['DATA_EXPLORATION_MODEL_ENGINE'] = args.model_engine

goal = "Using machine learning models and multivariate analysis find risk factors for diabetes. " \
       "Build predictive models to predict diabetes from health indicators.",

RUN_PARAMETERS = dict(
    project='diabetes',
    data_filenames=["diabetes_binary_health_indicators_BRFSS2015.csv"],
    research_goal=None,
    should_do_data_exploration=True,
)

if __name__ == '__main__':
    get_paper(**RUN_PARAMETERS,
              output_folder=args.output_folder,
              should_mock_servers=True,
              load_from_repo=True,
              save_on_repo=True)
