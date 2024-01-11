

# IMPORT
import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error
import pickle


# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')


# DATASET PREPARATIONS
# No dataset preparations are needed.


# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of age and weight stratified by sex"
df0 = df.groupby('sex').agg({'age_c':['mean', 'std'], 'wt':['mean', 'std']})
df0.index = ['Female', 'Male']
df0.to_pickle('table_0.pkl')


# PREPROCESSING 
# No preprocessing is needed, because the dataset is already clean and the features do not need to be transformed.


# ANALYSIS
# Table 1: "Comparison of the performance of the machine learning model and the formula-based model for predicting OTTD"
# ML model (Random forest)
X = df[['age_c', 'sex', 'ht', 'wt']]
y = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=0)
param_grid = {'n_estimators':[50, 100], 'max_depth': [2, None], 'min_samples_split': [2, 5]}
rf = RandomForestRegressor(random_state=0)
rf_cv = GridSearchCV(rf, param_grid, cv=5)
rf_cv.fit(X_train, y_train)
y_pred_rf = rf_cv.predict(X_test)
residuals_rf = y_test - y_pred_rf

# Formula-based model
y_pred_formula = X_test['ht'] / 10 + 5
residuals_formula = y_test - y_pred_formula

# Paired t-test
test_result = ttest_ind(residuals_rf, residuals_formula)

# DataFrame for Table 1
df1 = pd.DataFrame({
    'Model': ['Random Forest', 'Formula-based model'],
    'Mean Squared Residuals': [mean_squared_error(y_test, y_pred_rf), mean_squared_error(y_test, y_pred_formula)],
    't-statistic': [test_result.statistic, '-'],
    'p-value': [test_result.pvalue, '-']
})
df1.set_index('Model', inplace=True)
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0],
 'Best parameters for Random Forest model': rf_cv.best_params_
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
