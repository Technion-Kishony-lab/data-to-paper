

# IMPORT
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import numpy as np
from sklearn.model_selection import GridSearchCV
import pickle

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed, because the dataset is ready to be used by the machine learning model.

# ANALYSIS

## Table 1: Test of difference in predictive power between formula-based model 

# Separate features and target
features = data[['sex', 'age_c', 'ht', 'wt']].values
target = data['tube_depth_G'].values

# Train test split
features_train, features_test, target_train, target_test = train_test_split(
    features, target, test_size=0.2, random_state=42)

rf = RandomForestRegressor(random_state=42)
param_grid = {
    'n_estimators': [50, 100, 200],
    'min_samples_split': [2, 4, 8],
}
grid_search = GridSearchCV(estimator = rf, param_grid = param_grid)

grid_search.fit(features_train, target_train)
best_rf = grid_search.best_estimator_

# Prediction
rf_predictions = best_rf.predict(features_test)

# Compute residuals for RF model
rf_squared_residuals = (rf_predictions - target_test) ** 2

# Compute Formula-based model predictions for test set
formula_predictions_test = features_test[:, 2] / 10 + 5

# Compute residuals for Formula-based model
formula_squared_residuals = (formula_predictions_test - target_test) ** 2

# Perform paired t-test
ttest_res = ttest_rel(rf_squared_residuals, formula_squared_residuals)

table_1 = pd.DataFrame({
    'Model': ['Random Forest', 'Formula-based Model'],
    't-statistic': [ttest_res.statistic, ttest_res.statistic],
    'p-value': [ttest_res.pvalue, ttest_res.pvalue]
}, index=['Model 1', 'Model 2'])

# SAVE DATAFRAME
table_1.to_pickle('table_1.pkl')

## Table 2: RMSE of Formula-based model and the Random Forest model

rf_rmse = np.sqrt(mean_squared_error(target_test, rf_predictions))
formula_rmse = np.sqrt(mean_squared_error(target_test, formula_predictions_test))

table_2 = pd.DataFrame({
    'Model': ['Random Forest', 'Formula-based Model'],
    'RMSE': [rf_rmse, formula_rmse]
}, index=['Model 1', 'Model 2'])

table_2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data),
    'Best Random Forest parameters': grid_search.best_params_
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
