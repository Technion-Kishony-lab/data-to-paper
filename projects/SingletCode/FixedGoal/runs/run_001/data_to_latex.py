
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'auprc': ('AUPRC', 'Average Precision (area under the precision-recall curve)'),
    'auroc': ('AUROC', 'Receiver Operating Characteristic area'),
    'TNR': ('TNR', 'True Negative Rate'),
    'std': ('Std', 'Standard Deviation'),
    'mean': ('Mean', 'Average Value'),
    'DoubletFinder': ('DoubletFinder', 'DoubletFinder doublet detection algorithm'),
    'Scrublet': ('Scrublet', 'Scrublet doublet detection algorithm'),
    'hybrid': ('hybrid', 'Hybrid doublet detection algorithm'),
    'scDblFinder': ('scDblFinder', 'scDblFinder doublet detection algorithm'),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k))
mapping0.update({
    'TNR_x': ('TNR', 'True Negative Rate')
})
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of AUPRC, AUROC and TNR metrics stratified by doublet detection algorithm",
    label='table:descriptive_stats',
    note=None,
    legend=legend0)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = {
    'Metric': ('Metric', 'Metric used for performance evaluation: AUPRC, AUROC, TNR'),
    'F-statistic': ('F-statistic', 'F-statistic for ANOVA test'),
    'p-value': ('p-value', 'Probability Value'),
}
mapping1.update(shared_mapping)  # add shared_mappings into mapping1
# Filter out only relevant keys for table 1
mapping1 = {k: v for k, v in mapping1.items() if is_str_in_df(df1, k)}

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Comparisons of doublet detection algorithms performance",
    label='table:algorithm_comparisons',
    note=None,
    legend=legend1)

