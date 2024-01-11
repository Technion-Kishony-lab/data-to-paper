
# IMPORT
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GridSearchCV
from scipy.stats import ttest_rel

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of height and age_c stratified by sex"
df0 = df.groupby('sex')[['age_c', 'ht']].agg(['mean', 'std'])
df0.columns = [' '.join(col).strip() for col in df0.columns.values]
df0.index = df0.index.map({0:'Female', 1:'Male'})
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed.

# ANALYSIS
# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(df[['sex', 'age_c', 'ht', 'wt']], df['tube_depth_G'], test_size=0.2, random_state=0)

## Table 1: "Performance metrics of the Random Forest and ElasticNet models"
## Random Forest
rf = RandomForestRegressor(random_state=0)
param_grid_rf = {"n_estimators": np.arange(10, 61, 10), "max_depth": np.arange(1, 6)}
grid_search_rf = GridSearchCV(rf, param_grid=param_grid_rf, cv=3, n_jobs=-1)
grid_search_rf.fit(X_train, y_train)
rf_best_model = grid_search_rf.best_estimator_
predictions_rf = rf_best_model.predict(X_test)
mse_rf = mean_squared_error(y_test, predictions_rf)

## ElasticNet
en = ElasticNet(random_state=0)
param_grid_en = {'alpha': np.logspace(-4, 1, 6), 'l1_ratio': np.arange(0.1, 0.7, 0.2)}
grid_search_en = GridSearchCV(en, param_grid=param_grid_en, cv=3, n_jobs=-1)
grid_search_en.fit(X_train, y_train)
en_best_model = grid_search_en.best_estimator_
predictions_en = en_best_model.predict(X_test)
mse_en = mean_squared_error(y_test, predictions_en)

df1 = pd.DataFrame({
    "model": ["Random Forest", "ElasticNet"],
    "mse": [mse_rf, mse_en]
})
df1.set_index('model', inplace=True)
df1.to_pickle('table_1.pkl')

## Table 2: "Comparison of residuals of the Random Forest and ElasticNet models"
residuals_rf = (predictions_rf - y_test)**2
residuals_en = (predictions_en - y_test)**2
ttest_res = ttest_rel(residuals_rf, residuals_en)
df2 = pd.DataFrame({
    "statistic": [ttest_res.statistic],
    "pvalue": [ttest_res.pvalue]
}, index=['Comparison'])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df), 
 'Best parameters for Random Forest': grid_search_rf.best_params_,
 'Best parameters for ElasticNet': grid_search_en.best_params_
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
 