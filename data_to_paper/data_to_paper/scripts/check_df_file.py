import pickle

from data_to_paper.env import FOLDER_FOR_RUN
from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import \
    check_analysis_df, check_displayitem_df
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import InfoDataFrameWithSaveObjFuncCall

files_starting_with_df = list(FOLDER_FOR_RUN.glob('df*'))

if __name__ == '__main__':
    for filepath in files_starting_with_df:
        with open(filepath, 'rb') as file:
            df = pickle.load(file)
            assert isinstance(df, InfoDataFrameWithSaveObjFuncCall)
        if df.get_prior_filename() is None:
            issues = check_analysis_df(df, output_folder=FOLDER_FOR_RUN)
        else:
            issues = check_displayitem_df(df, output_folder=FOLDER_FOR_RUN)

        print(f'Issues with {filepath}:')
        for issue in issues:
            print(issue)
