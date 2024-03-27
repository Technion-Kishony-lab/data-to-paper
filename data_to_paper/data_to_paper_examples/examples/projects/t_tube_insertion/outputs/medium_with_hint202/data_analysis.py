
# IMPORT

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.weightstats import DescrStatsW
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error
import pickle

# LOAD DATA

data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS

# No dataset preparations are needed

# DESCRIPTIVE STATISTICS

## Table 0: "Descriptive statistics of tracheal tube depth stratified by sex"

df0 = data.groupby("sex").tube_depth_G.agg(['mean', 'std'])
df0.index = df0.index.map({0: 'female', 1: 'male'})
df0.to_pickle('table_0.pkl')

# PREPROCESSING

# Create dummy variables for categorical variables (sex).
data["is_male"] = (data["sex"] == 1).astype(int)

# ANALYSIS

## Table 1: "Performance comparison between Machine-Learning model and Formula-Based model"

# Prepare for model training
X = data[["is_male", "age_c", "ht", "wt"]]
y = data["tube_depth_G"]

# Machine-Learning Model (Random Forest)
param_grid = {'n_estimators': [50, 100, 150], 'max_depth': [5, 10, 15]}
rf = RandomForestRegressor()
grid_search = GridSearchCV(estimator = rf, param_grid = param_grid)
grid_search.fit(X, y)
best_grid = grid_search.best_estimator_

# Prediction by Machine-Learning Model (Random Forest)
y_pred_rf = best_grid.predict(X)

# Formula-Based model
y_pred_fb = data.ht / 10 + 5 

# Compare performance
mse_rf = mean_squared_error(y, y_pred_rf)
mse_fb = mean_squared_error(y, y_pred_fb)

df1 = pd.DataFrame({
    "model": ["Random Forest", "Formula-Based"],
    "mse": [mse_rf, mse_fb]
}, index=['Model 1', 'Model 2'])

df1.to_pickle('table_1.pkl')

## Table 2: "Comparison of residuals between Random Forest model and Formula-Based model"

# Calculate residuals
residuals_rf = y - y_pred_rf
residuals_fb = y - y_pred_fb

# Perform paired Wilcoxon test
res_test = stats.wilcoxon(residuals_rf, residuals_fb)

df2 = pd.DataFrame({
    "model": ["Random Forest", "Formula-Based"],
    "mean_residual": [np.mean(residuals_rf), np.mean(residuals_fb)],
    "p_value": [res_test.pvalue] * 2
}, index=['Model 1', 'Model 2'])

df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS

additional_results = {
 'Total number of observations': len(data), 
 'Best parameters for Random Forest model': best_grid.get_params(),
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
