
# IMPORT

import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind
import pickle


# LOAD DATA

df = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")


# DATASET PREPARATIONS

# No dataset preparations are needed.


# DESCRIPTIVE STATISTICS

# No descriptive statistics table is needed.


# PREPROCESSING

# No preprocessing is needed, because all the variables are already in the appropriate format.


# ANALYSIS

## Table 1: "Contingency Table for PrePost and EndotrachealSuction"

# Perform chi-square test for independence
contingency_table = pd.crosstab(df["PrePost"], df["EndotrachealSuction"])
contingency_table.index = ['Pre-policy', 'Post-policy']
chi2, p, dof, expected = chi2_contingency(contingency_table)
contingency_table["Chi-squared"] = chi2
contingency_table["p-value"] = p
# save the dataframe to pickle file
contingency_table.to_pickle('table_1.pkl')

## Table 2: "Comparison of APGAR5 Scores before and after the policy change"

# Perform t-test
group1 = df[df["PrePost"] == 0]["APGAR5"]
group2 = df[df["PrePost"] == 1]["APGAR5"]
t_stat, p_val = ttest_ind(group1, group2)
ttest_table = pd.DataFrame({"t-statistic": [t_stat], "p-value": [p_val]},
                           index=['APGAR5 score comparison'])
# save the dataframe to pickle file
ttest_table.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS

additional_results = {
 'Total number of observations': df.shape[0], 
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
