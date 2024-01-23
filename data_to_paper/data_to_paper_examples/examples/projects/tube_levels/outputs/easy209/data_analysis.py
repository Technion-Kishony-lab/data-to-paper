
# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of tube depth stratified by sex"
df0 = df.groupby('sex')['tube_depth_G'].agg(['mean', 'std'])
df0.index=['female', 'male']
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed, because the variables are all numeric and do not require any transformation.

# ANALYSIS
## Table 1: "Performance metrics of the RF and EN models"
# Splitting the data into train and test sets
X = df.drop(['tube', 'tube_depth_G'], axis=1)
y = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Standardization
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# RF
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train_scaled, y_train)
rf_y_pred = rf.predict(X_test_scaled)

# EN
en = ElasticNetCV(l1_ratio=[.1, .5, .7, .9, .95, .99, 1], cv=5, random_state=42)
en.fit(X_train_scaled, y_train)
en_y_pred = en.predict(X_test_scaled)

# Performance metrics
rf_mse = mean_squared_error(y_test, rf_y_pred)
en_mse = mean_squared_error(y_test, en_y_pred)

df1 = pd.DataFrame({
    'Model': ['Random Forest', 'Elastic Net'],
    'Mean Squared Error': [rf_mse, en_mse]
})
df1.set_index('Model', inplace=True)
df1.to_pickle('table_1.pkl')

## Table 2: "Paired t-test comparing the performance of the RF and EN models"
t_test_result = ttest_rel(rf_y_pred, en_y_pred)
df2 = pd.DataFrame({
    'Paired t-test': ['t-stats', 'p-value'],
    'Values': [t_test_result.statistic, t_test_result.pvalue]
})
df2.set_index('Paired t-test', inplace=True)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df), 
 'RF Model MSE': rf_mse,
 'EN Model MSE': en_mse,
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
