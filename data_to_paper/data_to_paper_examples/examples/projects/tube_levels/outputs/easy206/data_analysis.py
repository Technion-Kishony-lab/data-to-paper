

# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# Handle missing values
data.dropna(inplace=True)

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of sex, age, height, weight and OTTD"
descriptive_statistics = {
    'mean': data.mean(),
    'std': data.std()
}
df0 = pd.DataFrame(descriptive_statistics)
df0.to_pickle('table_0.pkl')

# PREPROCESSING
X = data[['sex', 'age_c', 'ht', 'wt']]
y = data['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# ANALYSIS
## Table 1: "Comparison of performance of the Random Forest and Elastic Net models based on their mean squared error in predicting the OTTD"
rf = RandomForestRegressor()
en = ElasticNet()

# Hyperparameter tuning using cross-validation
param_grid_rf = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 2, 4, 6],
    'random_state': [1]
}
param_grid_en = {
    'alpha': [0.1, 1, 10],
    'l1_ratio': [0.3, 0.5, 0.7],
    'random_state': [1]
}
clf_rf = GridSearchCV(rf, param_grid_rf, cv=3)
clf_en = GridSearchCV(en, param_grid_en, cv=3)

# Fit and predict
clf_rf.fit(X_train, y_train)
clf_en.fit(X_train, y_train)
rf_predictions = clf_rf.predict(X_test)
en_predictions = clf_en.predict(X_test)

# Mean Squared Error of Predictions
rf_mse = mean_squared_error(y_test, rf_predictions)
en_mse = mean_squared_error(y_test, en_predictions)

# Paired T-Test on Residuals
rf_residuals = y_test - rf_predictions
en_residuals = y_test - en_predictions
ttest_result = ttest_rel(rf_residuals, en_residuals)

df1 = pd.DataFrame(data={'Model': ['Random Forest', 'Elastic Net'], 'Mean Squared Error': [rf_mse, en_mse], 'P-value': [ttest_result.pvalue, ttest_result.pvalue]}, columns=['Model', 'Mean Squared Error', 'P-value'])
df1.set_index('Model', inplace=True)  # setting the 'Model' column as index for meaningful labels
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': data.shape[0], 
 'Number of training observations': X_train.shape[0],
 'Number of testing observations': X_test.shape[0]
}
with open('additional_results.pkl', 'wb') as f:
     pickle.dump(additional_results, f)
