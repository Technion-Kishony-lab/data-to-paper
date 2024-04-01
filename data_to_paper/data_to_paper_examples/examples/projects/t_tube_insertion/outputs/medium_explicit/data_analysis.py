
# IMPORT
import pandas as pd
import numpy as np
from sklearn.utils import resample
from scipy.stats import stats
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error
import pickle

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics are needed.

# PREPROCESSING
features = df[['sex', 'age_c', 'ht', 'wt']]
target = df['tube_depth_G']

# ANALYSIS
## Table 1: Comparison of performance between Machine Learning Model (Random Forest) and formula-based method
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.3, random_state=42)

param_grid = {'n_estimators': [10, 50, 100, 200],'max_depth':[None, 2, 5, 10]}
grid_rf = GridSearchCV(RandomForestRegressor(random_state=42), param_grid=param_grid, cv=5)
grid_rf.fit(X_train, y_train)

# Compute predictions using the optimized Random Forest Model
rf_pred = grid_rf.predict(X_test)

# Compute predictions using formula-based method
formula_based_pred = X_test['ht'] / 10 + 5

# Compute Mean Squared Error (MSE) for both models
rf_errors = np.square(rf_pred - y_test)
formula_based_errors = np.square(formula_based_pred - y_test)

# Compare MSEs with a paired t-Test
t_test_results = stats.ttest_rel(rf_errors, formula_based_errors)

df1 = pd.DataFrame({
    'Mean Squared Error': [np.mean(rf_errors), np.mean(formula_based_errors)],
    't-statistic': [t_test_results.statistic, t_test_results.statistic],
    'p-value': [t_test_results.pvalue, t_test_results.pvalue]
}, index=['Random Forest', 'Formula-Based'])
df1.to_pickle('table_1.pkl')

## Table 2: Correlation between variables 'sex', 'age', 'height', 'weight' and the target variable
correlations_list = []
for feature in features.columns:
    correlation_results = stats.pearsonr(df[feature], df['tube_depth_G'])
    correlations_list.append({
        'feature': feature, 
        'pearson_correlation': correlation_results.statistic, 
        'p_value': correlation_results.pvalue})

df2 = pd.DataFrame(correlations_list).set_index('feature')
df2.to_pickle('table_2.pkl')

## Table 3: "Feature importances from the Random Forest model, including confidence intervals"
rf_model = grid_rf.best_estimator_
feature_importances = rf_model.feature_importances_
n_iterations = 1000
bootstrap_feature_importances = np.zeros((len(X_train.columns), n_iterations))
for i in range(n_iterations):
    X_resample, y_resample = resample(X_train, y_train)
    rf_model.fit(X_resample, y_resample)
    bootstrap_feature_importances[:, i] = rf_model.feature_importances_
bootstrap_percentiles = np.percentile(bootstrap_feature_importances, [2.5, 97.5], axis=1)

df3 = pd.DataFrame({
    'Feature': X_train.columns,
    'Importance': feature_importances,
    'Lower 95% CI': bootstrap_percentiles[0, :],
    'Upper 95% CI': bootstrap_percentiles[1, :]
}).set_index('Feature')
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),
    'Best parameters for Random Forest model': grid_rf.best_params_,         
    'accuracy of Random Forest model': grid_rf.score(X_test, y_test)
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
