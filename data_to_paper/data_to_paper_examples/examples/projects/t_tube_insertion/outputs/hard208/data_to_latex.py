

# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# Define shared_mapping for labels that are common to all tables.
shared_mapping: AbbrToNameDef = { }

# Split shared_mapping to abbreviations-names mapping and names-definitions mapping
abbrs_to_names_common, defs_common = split_mapping(shared_mapping)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
# Define table1_mapping by adding some more abbreviation-name, abbreviation-definition pairs to shared_mapping
table1_mapping: AbbrToNameDef = shared_mapping | OrderedDict([
    ('Random Forest', ('RF', 'Random Forest Machine Learning Model')),
    ('Elastic Net', ('EN', 'Elastic Net Machine Learning Model')),
    ('Support Vector Machine', ('SVM', 'Support Vector Machine Learning Model')),
    ('Neural Network', ('NN', 'Neural Network Machine Learning Model')),
    ('Height Formula', ('HF', 'Height Formula-based Model')),
    ('Age Formula', ('AF', 'Age Formula-based Model')),
    ('ID Formula', ('IF', 'ID Formula-based Model')),
])

# Split table1_mapping to abbreviations-names mapping and names-definitions mapping
abbrs_to_names_table1, defs_table1 = split_mapping(table1_mapping)

# Rename the columns and the index of df using abbreviations-names mapping
df = df.rename(columns=abbrs_to_names_table1, index=abbrs_to_names_table1)

# Combine common defs with table-specific defs for legend
legend = OrderedDict(list(defs_common.items()) + list(defs_table1.items()))

# Save as Latex table
to_latex_with_note(
 df, 'table_1.tex',
 caption="Mean squared residuals of Machine Learning models, and Formula-based models in predicting Optimal Tracheal Tube Depth", 
 label='table:MSR',
 note="RF, EN, SVM and NN refer to different types of machine learning models. HF, AF and IF refer to different types of formula-based models.",
 legend=legend)

