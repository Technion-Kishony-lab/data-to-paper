
# IMPORT
import pandas as pd
import numpy as np
import scipy.stats as stats
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of height and age stratified by sex"
df0 = df.groupby('sex')[['ht', 'age_c']].agg(['mean', 'std'])
df0.index = ['Female', 'Male']
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because our data is already organized and clean.

# ANALYSIS
## Table 1: "Descriptive statistics of Height Formula-based Model residuals"
df1 = df.copy()
df1['predicted_OTTD_by_ht'] = df1['ht'] / 10 + 5
df1['residuals_by_ht'] = df1['tube_depth_G'] - df1['predicted_OTTD_by_ht']
df1_resid_stats = df1['residuals_by_ht'].agg(['mean', 'std']).to_frame().T
df1_resid_stats.index = ['Height Formula-based Model']
df1_resid_stats.to_pickle('table_1.pkl')

## Table 2: "Descriptive statistics of Age Formula-based Model residuals"
df2 = df.copy()
conditions = [
    (df2['age_c'] < 0.5),
    (df2['age_c'] >= 0.5) & (df2['age_c'] < 1),
    (df2['age_c'] >= 1) & (df2['age_c'] < 2),
    (df2['age_c'] >= 2)
]
choices = [9, 10, 11, 12 + df2['age_c'] * 0.5]
df2['predicted_OTTD_by_age'] = np.select(conditions, choices, default=9)
df2['residuals_by_age'] = df2['tube_depth_G'] - df2['predicted_OTTD_by_age']
df2_resid_stats = df2['residuals_by_age'].agg(['mean', 'std']).to_frame().T
df2_resid_stats.index = ['Age Formula-based Model']
df2_resid_stats.to_pickle('table_2.pkl')

## p-value of the difference in residuals
ttest_results = stats.ttest_rel(df1['residuals_by_ht'], df2['residuals_by_age'])
additional_results = {
 'Total number of observations': df.shape[0], 
 'Paired t-test statistic': ttest_results.statistic,
 'Paired t-test p-value': ttest_results.pvalue
}

# SAVE ADDITIONAL RESULTS
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
