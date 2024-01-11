

# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import ttest_rel
import pickle
from math import sqrt

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
## No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## No descriptive statistics table is needed.

# PREPROCESSING
features = df[['sex', 'age_c', 'ht', 'wt']]
target = df['tube_depth_G']

# Splitting the dataset
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

# ANALYSIS

## Table 1: "Comparison of Random Forest and Elastic Net model performance in predicting OTTD after hyperparameter tuning."

# Random Forest model with hyperparameter tuning
rf = RandomForestRegressor()
param_grid_rf = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 5, 10]
}
gs_rf = GridSearchCV(rf, param_grid_rf)
gs_rf.fit(X_train, y_train)
rf_predictions = gs_rf.predict(X_test)
rf_squared_errors = (y_test - rf_predictions) ** 2

# Elastic Net model with hyperparameter tuning
enet = ElasticNet()
param_grid_enet = {
    'alpha': [0.1, 0.5, 1.0],
    'l1_ratio': [0.1, 0.5, 1.0]
}
gs_enet = GridSearchCV(enet, param_grid_enet)
gs_enet.fit(X_train, y_train)
enet_predictions = gs_enet.predict(X_test)
enet_squared_errors = (y_test - enet_predictions) ** 2

# T-Test
ttest_results = ttest_rel(rf_squared_errors, enet_squared_errors)

# Results dataframe
results = {
    "Models": ["Random Forest", "Elastic Net"],
    "Mean Squared Error": [mean_squared_error(y_test, rf_predictions), mean_squared_error(y_test, enet_predictions)],
    "T-test P-value": [ttest_results.pvalue, ttest_results.pvalue]
}

df1 = pd.DataFrame(results)
df1.set_index('Models', inplace=True)  # to set "Models" as the index
df1.to_pickle('table_1.pkl')

## Table 2: "R squared score for Random Forest and Elastic Net models"

# DataFrame for R squared scores
df2 = pd.DataFrame({
    'Models': ['Random Forest', 'Elastic Net'],
    'R Squared Score': [r2_score(y_test, rf_predictions), r2_score(y_test, enet_predictions)]
})
df2.set_index('Models', inplace=True)
df2.to_pickle('table_2.pkl')

## Table 3: "Root Mean Squared Error for Random Forest and Elastic Net models"

# DataFrame for Root Mean Squared Error (RMSE)
df3 = pd.DataFrame({
    'Models': ['Random Forest', 'Elastic Net'],
    'RMSE': [sqrt(mean_squared_error(y_test, rf_predictions)), sqrt(mean_squared_error(y_test, enet_predictions))]
})
df3.set_index('Models', inplace=True)
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
 'Random Forest Mean Squared Error': mean_squared_error(y_test, rf_predictions),
 'Elastic Net Mean Squared Error': mean_squared_error(y_test, enet_predictions)
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
 
 