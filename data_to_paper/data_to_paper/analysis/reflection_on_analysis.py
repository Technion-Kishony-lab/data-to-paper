import os
import pickle
import subprocess
from io import BytesIO
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_prefixed_pickle_file_paths_in_branch(branch, prefix, file_name):
    """
    Get all the pkl files that start with the given prefix in the given branch.
    Returns a dict mapping the folder name to the path of the text file.
    using git ls-tree and not git checkout
    """
    list_all_pkl_files_command = f'git ls-tree --name-only -r {branch} | grep {prefix}'
    # run the command
    output = os.popen(list_all_pkl_files_command).read()
    # split the output to lines
    lines = output.split('\n')
    # remove empty lines and keep lines that end with file_name
    paths_to_all_pkl_files = ['data_to_paper/' + line for line in lines if line.endswith(file_name)]
    return paths_to_all_pkl_files


def get_reflection_scores(path_to_pkl_file: str, branch: str):
    """
    Get data from a .pkl file located in a specific git branch.
    """
    # Execute the 'git show' command and capture the binary output
    pkl_file_content = subprocess.check_output(['git', 'show', f'{branch}:{path_to_pkl_file}'])

    # Use BytesIO to treat the binary content as a file-like object
    pkl_file_like_object = BytesIO(pkl_file_content)

    # Deserialize the .pkl file content
    data = pickle.load(pkl_file_like_object)

    return data


def extract_reflection_scores_from_branch(branch, prefix):
    """
    Get all the dict scores from the given branch and prefix.
    """
    paths_to_all_reflection_pickle_files = get_prefixed_pickle_file_paths_in_branch(
        branch, prefix, 'reflection_on_analysis.pkl')
    reflection_scores = {}
    for data_analysis_file_path in paths_to_all_reflection_pickle_files:
        # get the code length for the given file, the name of the paper is the folder name
        reflection_scores[data_analysis_file_path.split('/')[-2]] = (
            get_reflection_scores(data_analysis_file_path, branch))
    return reflection_scores


def extract_reflection_scores_from_branches(branches, prefixes):
    """
    Get all the reflection scores from the given branches and prefixes.
    """
    reflection_scores_for_all_branches = {}
    for branch, prefix in zip(branches, prefixes):
        reflection_scores_for_all_branches[f'{branch}/{prefix}'] = (
            extract_reflection_scores_from_branch(branch, prefix))
    return reflection_scores_for_all_branches


def get_all_reflection_scores():
    """
    Get all the reflection scores from all the branches and prefixes.
    """
    # chdir to the root of the project
    os.chdir('../..')
    branches = ['examples/tube_levels',
                'examples/tube_levels',
                'examples/tube_levels',
                'examples/nicu',
                'examples/diabetes',
                'examples/congress_social_network'
                ]
    prefixes = ['easy_with_hint2',
                'medium_with_hint2',
                'hard_with_hint2',
                'paper2',
                'paper13',
                'open_goal_accum'
                ]
    reflection_scores_for_all_branches = extract_reflection_scores_from_branches(branches, prefixes)
    return reflection_scores_for_all_branches


if __name__ == '__main__':
    reflection_scores_for_all_branches = get_all_reflection_scores()
    if not os.path.exists(os.path.join(MODULE_DIR, 'outputs')):
        os.mkdir(os.path.join(MODULE_DIR, 'outputs'))
    reflection_scores_for_all_branches_df = pd.DataFrame(reflection_scores_for_all_branches)
    reflection_scores_for_all_branches_df = (reflection_scores_for_all_branches_df.melt(ignore_index=False).
    reset_index().rename(columns={'index': 'paper', 'variable': 'dataset', 'value': 'scores'}))
    reflection_scores_for_all_branches_df['dataset'] = reflection_scores_for_all_branches_df['dataset'].apply(
        lambda x: x.split('/')[1])
    reflection_scores_for_all_branches_df = (
        reflection_scores_for_all_branches_df.join(pd.json_normalize(reflection_scores_for_all_branches_df['scores'])))
    reflection_scores_for_all_branches_df = reflection_scores_for_all_branches_df.drop(columns=['scores'])
    # reorder the columns such that the dataset and paper columns are the first two columns
    reflection_scores_for_all_branches_df = reflection_scores_for_all_branches_df[
        ['dataset', 'paper'] + [col for col in reflection_scores_for_all_branches_df.columns if col not in
                                ['paper', 'dataset']]]
    # save the reflection scores to a csv file after dropping rows with NaN values
    (reflection_scores_for_all_branches_df.dropna().reset_index(drop=True).to_csv
     (os.path.join(MODULE_DIR, 'outputs/reflection_scores.csv')))
