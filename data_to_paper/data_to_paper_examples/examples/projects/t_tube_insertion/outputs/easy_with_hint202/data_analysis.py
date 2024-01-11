
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle
import warnings
warnings.filterwarnings('ignore')

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Mean and standard deviation of patient features and tube_depth_G stratified by sex"
df0 = df.groupby('sex').agg(['mean','std']).transpose()
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because all the features are numerical and there are no missing values.

# ANALYSIS
# Determining feature and target variables
X = df[["sex", "age_c", "ht", "wt"]]
y = df["tube_depth_G"]

# Splitting the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Table 1: "Performance (mean squared error) of Random Forest and Elastic Net models on the test set"
# Hyperparameter tuning for Random Forest
rf = RandomForestRegressor(random_state=42)
param_grid = {
    'n_estimators': [200, 500],
    'max_features': ['sqrt', 'log2']
}
CV_rf = GridSearchCV(estimator=rf, param_grid=param_grid, cv= 2)
CV_rf.fit(X_train, y_train)
best_rf = CV_rf.best_estimator_
rf_pred = best_rf.predict(X_test)
rf_mse = mean_squared_error(y_test, rf_pred)

# Hyperparameter tuning for Elastic Net
en = ElasticNet(random_state=42)
param_grid = {
    'alpha' : [0.1, 0.5, 1, 2, 5],
    'l1_ratio' : [0.1, 0.5, 1]
}
CV_en = GridSearchCV(en, param_grid=param_grid, cv=2)
CV_en.fit(X_train, y_train)
best_en = CV_en.best_estimator_
en_pred = best_en.predict(X_test)
en_mse = mean_squared_error(y_test, en_pred)

df1 = pd.DataFrame({'Model': ['Random Forest', 'Elastic Net'], 'Mean Squared Error': [rf_mse, en_mse]})
df1.set_index('Model', inplace=True)
df1.to_pickle('table_1.pkl')

# Table 2: "Paired t-test comparing the squared residuals of the two models"
rf_res = (rf_pred - y_test)**2
en_res = (en_pred - y_test)**2
ttest_results = ttest_rel(rf_res, en_res)
df2 = pd.DataFrame({'Model 1 residuals': ['Random Forest'], 'Model 2 residuals': ['Elastic Net'], 't statistic': [ttest_results.statistic], 'p value': [ttest_results.pvalue]})
df2.set_index('Model 1 residuals', inplace=True)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
 'Best parameters of Random Forest model': CV_rf.best_params_,
 'Best parameters of Elastic Net model': CV_en.best_params_
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
