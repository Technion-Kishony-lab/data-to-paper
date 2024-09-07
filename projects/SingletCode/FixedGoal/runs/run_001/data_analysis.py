
# IMPORT
import pickle
import pandas as pd
import numpy as np
import scipy.stats as stats

# LOAD DATA
file1 = pd.read_csv("barcodedNonBarcoded_AUPRC_AUROC_TNR.csv")
file2 = pd.read_csv("TNR_plotted_formatted.csv")

# DATASET PREPARATIONS
data = pd.merge(file1, file2, how='inner', on=['dataset', 'sample', 'condition'])
data.drop(['Unnamed: 0_x', 'Unnamed: 0_y', 'X_x', 'X_y'], axis=1, inplace=True)  # Drop irrelevant columns
data = data.dropna()  # Drop any rows with missing data

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of AUPRC, AUROC and TNR metrics stratified by condition"
df0 = data.groupby('condition')[['auprc', 'auroc', 'TNR_x']].agg(['mean', 'std'])
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed, because all necessary transformations and standardizations have been done in the dataset preparations section.

# ANALYSIS
## Table 1: "Comparisons of doublet detection algorithms performance"
algorithms = data['condition'].unique()
auprc_f_oneway = stats.f_oneway(*(data['auprc'][data['condition'] == alg] for alg in algorithms))
auroc_f_oneway = stats.f_oneway(*(data['auroc'][data['condition'] == alg] for alg in algorithms))
TNR_f_oneway = stats.f_oneway(*(data['TNR_x'][data['condition'] == alg] for alg in algorithms))

df1 = pd.DataFrame({
    'Metric': ['auprc', 'auroc', 'TNR'],
    'F-statistic': [auprc_f_oneway.statistic, auroc_f_oneway.statistic, TNR_f_oneway.statistic],
    'p-value': [auprc_f_oneway.pvalue, auroc_f_oneway.pvalue, TNR_f_oneway.pvalue]
    })

str_metric = df1['Metric'].astype(str)
df1.insert(0, 'Metric_String', str_metric)
df1.set_index('Metric_String', inplace=True)
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data)
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
