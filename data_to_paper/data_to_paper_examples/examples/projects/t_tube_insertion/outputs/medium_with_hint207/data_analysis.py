
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
import pickle

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of height and age stratified by sex"
df0 = data.groupby('sex').agg({'ht':['mean', 'std'], 'age_c':['mean', 'std']})
df0.index = ['Female', 'Male']
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed.

# ANALYSIS
## Table 1: "Comparison of predictive power: ML model vs. Formula-based model"
# Define target and features 
target = data['tube_depth_G']
features = data[['sex', 'age_c', 'ht', 'wt']]

# split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.3, random_state=0)

# Define the Random Forest model
rf = RandomForestRegressor()

# define parameters for GridSearchCV
param_grid = {'n_estimators': [50, 100], 'max_depth': [None, 5, 10], 'min_samples_split': [2, 5]}

# Perform hyperparameter tuning 
grid = GridSearchCV(rf, param_grid, cv=5)
grid.fit(X_train, y_train)

# Predict with ML model
ml_preds = grid.predict(X_test)

# Predict with formula-based model
fb_preds = X_test['ht'] / 10 + 5

# Compute square residuals
ml_sq_res = np.square(ml_preds - y_test)
fb_sq_res = np.square(fb_preds - y_test)

# Perform paired t-test
t_results = stats.ttest_rel(ml_sq_res, fb_sq_res)

# Create Table 1's DataFrame
df1 = pd.DataFrame({'Model': ['ML Model', 'Formula-based Model'],
                    'Mean Squared Residual': [ml_sq_res.mean(), fb_sq_res.mean()],
                    'p-value': [t_results.pvalue, '-']})

df1.set_index('Model', inplace=True)
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
rf_train_score = grid.score(X_train, y_train)
rf_test_score = grid.score(X_test, y_test)
best_params = grid.best_params_
additional_results = {
 'RF train score': rf_train_score, 
 'RF test score': rf_test_score, 
 'RF best parameters': best_params
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

