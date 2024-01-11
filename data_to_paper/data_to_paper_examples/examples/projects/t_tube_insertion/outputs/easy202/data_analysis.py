

# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
features = df[['sex', 'age_c', 'ht', 'wt']]
target = df['tube_depth_G']

# Normalize the features
scaler = StandardScaler()
features = scaler.fit_transform(features)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(features, target, random_state=42)

# ANALYSIS

## Table 1: "Mean and Std of Squared residuals of the Random Forest model and the Elastic Net model"
rf = RandomForestRegressor(random_state=42)
params_rf = {'n_estimators': [50, 100, 200], 'max_depth': [None, 5, 10]}
grid_rf = GridSearchCV(estimator=rf, param_grid=params_rf, cv=5)
grid_rf.fit(X_train, y_train)
rf_best = grid_rf.best_estimator_
pred_rf = rf_best.predict(X_test)
residuals_rf = (y_test - pred_rf)**2

en = ElasticNetCV(cv=5, random_state=42)
en.fit(X_train, y_train)
pred_en = en.predict(X_test)
residuals_en = (y_test - pred_en)**2

df1 = pd.DataFrame({
    'RF_Mean_Squared_Residuals': residuals_rf.mean(),
    'RF_Std_Squared_Residuals' : residuals_rf.std(),
    'EN_Mean_Squared_Residuals': residuals_en.mean(),
    'EN_Std_Squared_Residuals' : residuals_en.std(),
    }, index=['Model Performance'])
df1.to_pickle('table_1.pkl')

## Table 2: "Paired t-test results between means of Random Forest and Elastic Net squared residuals"
res_diff_test = ttest_rel(residuals_rf, residuals_en)

df2 = pd.DataFrame({ 't_stat': [res_diff_test.statistic], 'p_value': [res_diff_test.pvalue] }, index=['Paired t-test'])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
rmse_rf = np.sqrt(mean_squared_error(y_test, pred_rf))
rmse_en = np.sqrt(mean_squared_error(y_test, pred_en))

additional_results = {
 'Total number of observations': len(df),
 'RMSE of Random Forest model': rmse_rf,
 'RMSE of Elastic Net model': rmse_en
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)

