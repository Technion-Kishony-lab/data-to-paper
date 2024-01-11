
# IMPORT 
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.


# DESCRIPTIVE STATISTICS
# Table 0: Descriptive statistics of patient features and OTTD
desc_stats_df = df[['sex', 'age_c', 'ht', 'wt', 'tube_depth_G']].agg(['mean', 'std'])
desc_stats_df.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed, because the dataset does not contain any non-numeric variables.

# Splitting the dataset into train and test sets
features = df[['sex', 'age_c', 'ht', 'wt']]
target = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

# ANALYSIS

# Table 1: Mean squared residuals for Random Forest and Elastic Net
rf_model = RandomForestRegressor()
rf_model.fit(X_train, y_train)
rf_predictions = rf_model.predict(X_test)
rf_residuals = np.square(rf_predictions - y_test)

en_model = ElasticNetCV()
en_model.fit(X_train, y_train)
en_predictions = en_model.predict(X_test)
en_residuals = np.square(en_predictions - y_test)

# Revised df1 to include model names as the index
df1 = pd.DataFrame({
  'Model': ['Random Forest', 'Elastic Net'],
  'Mean Squared Residual': [rf_residuals.mean(), en_residuals.mean()]
}).set_index('Model')
df1.to_pickle('table_1.pkl')


# Table 2: Paired t-test results for the mean squared residuals of Random Forest and Elastic Net
ttest_res = ttest_rel(rf_residuals, en_residuals) 

# Revised df2 to include comparison descriptor as the index
df2 = pd.DataFrame({
    'Model Comparison': ['RF vs EN Mean Squared Residuals'],
    't-statistic': [ttest_res.statistic],
    'p-value': [ttest_res.pvalue]
}).set_index('Model Comparison')

df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df), 
    'Training set size': len(X_train),
    'Testing set size': len(X_test) 
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
