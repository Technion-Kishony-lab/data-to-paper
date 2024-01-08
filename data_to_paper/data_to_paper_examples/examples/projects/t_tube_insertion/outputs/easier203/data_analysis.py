
# IMPORT
import pandas as pd
import numpy as np
import scipy.stats as stats
from sklearn.metrics import mean_squared_error
import pickle

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: Average and standard deviation of height and age stratified by sex
grouped = data.groupby('sex')
means = grouped[['ht', 'age_c']].mean().rename(columns={'ht': 'Average Height', 'age_c': 'Average Age'})
stds = grouped[['ht', 'age_c']].std().rename(columns={'ht': 'Standard Deviation - Height', 'age_c': 'Standard Deviation - Age'})
df0 = pd.concat([means, stds], axis=1)
df0.index.names = ['Sex']
df0.index = df0.index.astype(str) # convert index to string
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed

# ANALYSIS
## Table 1: Mean and standard deviation of residuals 
data['predicted_ht'] = data['ht'] / 10 + 5
data['residuals_ht'] = np.abs(data['predicted_ht'] - data['tube_depth_G'])
data['predicted_age'] = np.select([(data['age_c'] < 0.5), 
                                    (data['age_c'] >= 0.5) & (data['age_c'] < 1),
                                    (data['age_c'] >= 1) & (data['age_c'] < 2),
                                    (data['age_c'] >= 2)],
                                   [9, 10, 11, 12 + data['age_c'] * 0.5])
data['residuals_age'] = np.abs(data['predicted_age'] - data['tube_depth_G'])

df1 = pd.DataFrame({'Mean Residuals - Height Based Model': [data['residuals_ht'].mean()], 
                    'Standard Deviation Residuals - Height Based Model': [data['residuals_ht'].std()], 
                    'Mean Residuals - Age Based Model': [data['residuals_age'].mean()], 
                    'Standard Deviation Residuals - Age Based Model': [data['residuals_age'].std()]},
                   index=['Model Residuals'])
df1.to_pickle('table_1.pkl')

## Table 2: RMSE of the models
RMSE_HT = np.sqrt(mean_squared_error(data['tube_depth_G'], data['predicted_ht']))
RMSE_Age = np.sqrt(mean_squared_error(data['tube_depth_G'], data['predicted_age']))
df2 = pd.DataFrame({'RMSE': [RMSE_HT, RMSE_Age]}, index=['Height-based Model', 'Age-based Model'])
df2.to_pickle('table_2.pkl')

## Table 3: Paired t-Test Residuals
t_test_result = stats.ttest_rel(data['residuals_ht'], data['residuals_age'])
df3 = pd.DataFrame({'Model':['Height-based Model vs Age-based Model'], 't-value':[t_test_result.statistic], 'p-value':[t_test_result.pvalue]})
df3 = df3.set_index('Model')
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': data.shape[0],
 'Mean HT prediction': data['predicted_ht'].mean(),
 'Mean Age prediction': data['predicted_age'].mean()
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
