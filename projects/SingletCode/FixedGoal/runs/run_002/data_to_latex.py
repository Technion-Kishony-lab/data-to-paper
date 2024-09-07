
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Optional, Dict, Any, Tuple 

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Mean AUPRC': ('Avg. AUPRC', 'Average Area Under Precision-Recall Curve'),
    'Mean AUROC': ('Avg. AUROC', 'Average Area Under Receiver Operating Characteristics Curve'),
    'Mean TNR': ('Avg. TNR', 'Average True Negative rate'),
    'STD AUPRC': ('StdDev AUPRC', 'Standard Deviation of AUPRC'),
    'STD AUROC': ('StdDev AUROC', 'Standard Deviation of AUROC'),
    'STD TNR': ('StdDev TNR', 'Standard Deviation of TNR'),
    'Mean dbl_act': ('Avg. Act. Doublet Rate', 'Average actual doublet rate'),
    'Mean dbl_exp': ('Avg. Exp. Doublet Rate', 'Average expected doublet rate'),
    'STD dbl_act': ('StdDev Act. Doublet Rate', 'Standard Deviation of the actual doublet rate'),
    'STD dbl_exp': ('StdDev Exp. Doublet Rate', 'Standard Deviation of the expected doublet rate'),
    'condition': (None, 'Condition Applied: DoubletFinder, hybrid, scDblFinder or Scrublet')
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# TRANSPOSE THE DATASET
df0 = df0.T

# RENAME ROWS AND COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k)) 
mapping0 |= {
    'condition': ('Condition', None),
    'DoubletFinder': ('DbltFndr', 'Doublet Finder Algorithm'),
    'Scrublet': ('Scrblt', 'Scrublet Algorithm'),
    'hybrid': ('hyb', 'Hybrid Algorithm'),
    'scDblFinder': ('scDBlFndr', 'scDblFinder Algorithm'),
}
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX:
to_latex_with_note(
    df0, 'table_0.tex',
    caption='Descriptive statistics of performance metrics stratified by condition', 
    label='table:table_0',
    note=None,
    legend=legend0)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {'AUPRC': ('AUPRC', 'Area Under Precision-Recall Curve')}

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption='ANOVA results comparing Area Under Precision-Recall Curve (AUPRC) across algorithms', 
    label='table:table_1',
    note=None,
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {'AUROC': ('AUROC', 'Area Under Receiver Operating Characteristics Curve')}

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex',
    caption='ANOVA results comparing Area Under Receiver Operating Characteristic (AUROC) across algorithms', 
    label='table:table_2',
    note=None,
    legend=legend2)

# TABLE 3:
df3 = pd.read_pickle('table_3.pkl')

# RENAME ROWS AND COLUMNS
mapping3 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df3, k)) 
mapping3 |= {'TNR': ('TNR', 'True Negative Rate')}

abbrs_to_names3, legend3 = split_mapping(mapping3)
df3 = df3.rename(columns=abbrs_to_names3, index=abbrs_to_names3)

# SAVE AS LATEX:
to_latex_with_note(
    df3, 'table_3.tex',
    caption='Kruskal-Wallis results comparing True Negative Rate (TNR) across algorithms', 
    label='table:table_3',
    note=None,
    legend=legend3)
