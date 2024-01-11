
# IMPORT
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle
import numpy as np

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
features = df[['sex', 'age_c', 'ht', 'wt']].values
target = df['tube_depth_G'].values
tr_X, test_X, tr_y, test_y = train_test_split(features, target, train_size=0.8, random_state=42)

# ANALYSIS
## Table 1: "Average Residuals and Their Standard Deviations for Random Forest and Elastic Net Models"
# Initialize models with default parameters
rf = RandomForestRegressor(random_state=42)
en = ElasticNet(random_state=42)

# GridSearchCV for hyperparameter tuning
parameter_grid_rf = {'n_estimators': [100, 200], 'max_depth': [None, 5, 10]}
parameter_grid_en = {'alpha': [0.1, 0.5, 1], 'l1_ratio': [0.1, 0.5, 1]}

gs_rf = GridSearchCV(rf, parameter_grid_rf, cv = 5)
gs_rf.fit(tr_X, tr_y)
gs_en = GridSearchCV(en, parameter_grid_en, cv = 5)
gs_en.fit(tr_X, tr_y)

rf_best = gs_rf.best_estimator_
en_best = gs_en.best_estimator_

# Now, apply these models to the test set and calculate residuals
residuals_rf = test_y - rf_best.predict(test_X)
residuals_en = test_y - en_best.predict(test_X)

# Now, create a dataframe with the mean and std of these residuals and save the dataframe
df1 = pd.DataFrame({
    'rf_residuals_mean': [np.mean(residuals_rf)], 
    'rf_residuals_std': [np.std(residuals_rf)],
    'en_residuals_mean': [np.mean(residuals_en)], 
    'en_residuals_std': [np.std(residuals_en)]}, 
    index=['Residuals'])
df1.to_pickle('table_1.pkl')

## Table 2: "Paired T-test Results for Squared Residuals of the Two Models"
# Now, we perform the paired t-test in order to see whether the squared residuals are significantly different
t_results = ttest_rel(residuals_rf**2, residuals_en**2)

df2 = pd.DataFrame({'t_statistic': [t_results.statistic], 'p_value': [t_results.pvalue]}, 
                   index=['Paired t-test'])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0], 
    'Accuracy of RF model': rf_best.score(test_X, test_y),
    'Accuracy of EN model': en_best.score(test_X, test_y)
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
