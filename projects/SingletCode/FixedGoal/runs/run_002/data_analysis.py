
# IMPORT
import pandas as pd
import numpy as np
import pickle
from scipy.stats import f_oneway, kruskal
from sklearn.preprocessing import LabelEncoder

# LOAD DATA
file1 = pd.read_csv('barcodedNonBarcoded_AUPRC_AUROC_TNR.csv')
file2 = pd.read_csv('TNR_plotted_formatted.csv')

# DATASET PREPARATIONS
df = pd.merge(file1, file2, on=['sample', 'dataset', 'condition'], how='inner')
df = df.dropna()

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of AUPRC, AUROC, and TNR stratified by condition"
desc_stat = df.groupby('condition')[['auprc', 'auroc', 'TNR_x', 'dbl_act_x', 'dbl_exp']].mean()
desc_stat.columns = ['Mean AUPRC', 'Mean AUROC', 'Mean TNR', 'Mean dbl_act', 'Mean dbl_exp']
desc_stat_std = df.groupby('condition')[['auprc', 'auroc', 'TNR_x', 'dbl_act_x', 'dbl_exp']].std()
desc_stat_std.columns = ['STD AUPRC', 'STD AUROC', 'STD TNR', 'STD dbl_act', 'STD dbl_exp']
df0 = pd.concat([desc_stat, desc_stat_std], axis=1)
df0.to_pickle('table_0.pkl')

# PREPROCESSING
labelencoder = LabelEncoder()
df['condition_code'] = labelencoder.fit_transform(df['condition'])

# ANALYSIS
## Table 1: "ANOVA results comparing AUPRC across algorithms"
auprc_results = f_oneway(df['auprc'][df['condition'] == 'DoubletFinder'],
                         df['auprc'][df['condition'] == 'hybrid'],
                         df['auprc'][df['condition'] == 'scDblFinder'],
                         df['auprc'][df['condition'] == 'Scrublet'])
df1 = pd.DataFrame({'F-value': [auprc_results.statistic], 'P-value': [auprc_results.pvalue]}, index=['AUPRC'])
df1['Best Algorithm'] = desc_stat['Mean AUPRC'].idxmax()
df1.to_pickle('table_1.pkl')

## Table 2: "ANOVA results comparing AUROC across algorithms"
auroc_results = f_oneway(df['auroc'][df['condition'] == 'DoubletFinder'],
                         df['auroc'][df['condition'] == 'hybrid'],
                         df['auroc'][df['condition'] == 'scDblFinder'],
                         df['auroc'][df['condition'] == 'Scrublet'])
df2 = pd.DataFrame({'F-value': [auroc_results.statistic], 'P-value': [auroc_results.pvalue]}, index=['AUROC'])
df2['Best Algorithm'] = desc_stat['Mean AUROC'].idxmax()
df2.to_pickle('table_2.pkl')

## Table 3: "Kruskal-Wallis results comparing TNR across algorithms"
tnr_results = kruskal(df['TNR_x'][df['condition'] == 'DoubletFinder'],
                      df['TNR_x'][df['condition'] == 'hybrid'],
                      df['TNR_x'][df['condition'] == 'scDblFinder'],
                      df['TNR_x'][df['condition'] == 'Scrublet'])
df3 = pd.DataFrame({'H-value': [tnr_results.statistic], 'P-value': [tnr_results.pvalue]}, index=['TNR'])
df3['Best Algorithm'] = desc_stat['Mean TNR'].idxmax()
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0]
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
