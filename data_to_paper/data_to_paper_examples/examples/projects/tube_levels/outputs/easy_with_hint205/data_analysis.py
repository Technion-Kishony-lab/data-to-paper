
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error
import pickle

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# No preprocessing is needed, because the provided features are already numerical.

# ANALYSIS
X = df[['sex', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create Regressor with Grid Search for RandomForest
rf_regressor = RandomForestRegressor(random_state=42)
grid_values_rf = {'n_estimators': [50, 100], 'max_depth' : [None, 7, 10], 'min_samples_leaf' : [1, 2]}
grid_search_rf = GridSearchCV(rf_regressor, param_grid = grid_values_rf, scoring = 'neg_mean_squared_error', cv = 5)
grid_search_rf.fit(X_train, y_train)

# Create Regressor with Grid Search for ElasticNet
en_regressor = ElasticNet(random_state=42)
grid_values_en = {'alpha': [0.001, 0.01, 0.1, 1], 'l1_ratio': [0.5, 0.7, 1]}
grid_search_en = GridSearchCV(en_regressor, param_grid = grid_values_en, scoring = 'neg_mean_squared_error', cv =5)
grid_search_en.fit(X_train, y_train)

# Predictions
rf_predictions = grid_search_rf.best_estimator_.predict(X_test)
en_predictions = grid_search_en.best_estimator_.predict(X_test)

# residuals
rf_resid = (rf_predictions - y_test) ** 2
en_resid = (en_predictions - y_test) ** 2

## Table 1: "Summary statistics of squared residuals for Random Forest and Elastic Net models"
table_1 = {'Mean Squared Residuals': [np.mean(rf_resid), np.mean(en_resid)],
           'Std. Dev. Squared Residuals': [np.std(rf_resid), np.std(en_resid)]}
labels = ['Random Forest', 'Elastic Net']

df1 = pd.DataFrame(table_1, index=labels)
df1.to_pickle('table_1.pkl')

# Perform paired t-test
ttest_results = stats.ttest_rel(rf_resid, en_resid)

## Table 2: "Best hyperparameters for Random Forest and Elastic Net models"
table_2 = {'Random Forest': [str(grid_search_rf.best_params_)],
           'Elastic Net': [str(grid_search_en.best_params_)]}
labels = ['Hyperparameters']

df2 = pd.DataFrame(table_2, index=labels)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df), 
 'RF model MSE': mean_squared_error(y_test, rf_predictions),
 'EN model MSE': mean_squared_error(y_test, en_predictions),
 'Paired t-test statistic': ttest_results.statistic,
 'Paired t-test p-value': ttest_results.pvalue
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
