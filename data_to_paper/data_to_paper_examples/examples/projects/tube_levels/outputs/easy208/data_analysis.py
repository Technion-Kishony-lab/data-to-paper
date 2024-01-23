
# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import scipy.stats as stats
import pickle

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
desc_stats = data[['sex', 'age_c', 'ht', 'wt', 'tube_depth_G']].describe().loc[['mean', 'std']]
desc_stats.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because all the data features are already numeric.

# ANALYSIS
## Table 1: "Descriptive statistics of age, sex, height, weight, and OTTD"
df1 = desc_stats
df1.to_pickle('table_1.pkl')

# Model preparation
features = data[['sex', 'age_c', 'ht', 'wt']]
target = data['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.3, random_state=0)

# RF model
rf_model = RandomForestRegressor(random_state=1)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)

## Table 2: "RF model performance: MSE"
df2 = pd.DataFrame({'RF_MSE': [mean_squared_error(y_test, rf_pred)]}, index=['Random Forest'])
df2.to_pickle('table_2.pkl')

# EN model
en_model = ElasticNetCV(cv=5, l1_ratio=[.1, .5, .7, .9, .95, .99, 1])
en_model.fit(X_train, y_train)
en_pred = en_model.predict(X_test)

## Table 3: "EN model performance: MSE"
df3 = pd.DataFrame({'EN_MSE': [mean_squared_error(y_test, en_pred)]}, index=['Elastic Net'])
df3.to_pickle('table_3.pkl')

# Hypothesis test
t_test_result = stats.ttest_rel((rf_pred - y_test) ** 2, (en_pred - y_test) ** 2)

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data), 
    't_stat for hypothesis test': t_test_result.statistic,
    'p_val for hypothesis test': t_test_result.pvalue
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
