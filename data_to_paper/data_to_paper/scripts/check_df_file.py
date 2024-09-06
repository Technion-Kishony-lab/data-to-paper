import pickle

from data_to_paper.env import FOLDER_FOR_RUN
from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import \
    check_analysis_df, check_displayitem_df

files_starting_with_df = list(FOLDER_FOR_RUN.glob('df*'))

if __name__ == '__main__':
    for filepath in files_starting_with_df:
        with open(filepath, 'rb') as file:
            df = pickle.load(file)
        if len(df.extra_info) == 1:
            issues = check_analysis_df(df, output_folder=FOLDER_FOR_RUN)
        elif len(df.extra_info) == 2:
            issues = check_displayitem_df(df, output_folder=FOLDER_FOR_RUN)
        else:
            raise ValueError(f'Unexpected number of extra_info elements: {len(df.extra_info)}')

        print(f'Issues with {filepath}:')
        for issue in issues:
            print(issue)
