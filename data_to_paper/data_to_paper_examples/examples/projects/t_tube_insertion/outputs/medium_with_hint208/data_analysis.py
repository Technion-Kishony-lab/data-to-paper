
# IMPORT
import pandas as pd
import numpy as np
import pickle
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of tube_depth_G stratified by sex"
df0 = df.groupby('sex').tube_depth_G.agg(['mean', 'std'])
df0.index = ['female', 'male']
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed, because all the variables are already in suitable format.

# ANALYSIS
## Table 1: "Model performance comparison: Random Forest vs. Height-based Formula"
# Random Forest
X = df[["sex", "age_c", "ht", "wt"]]
y = df["tube_depth_G"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf = RandomForestRegressor(random_state=42)
param_grid = {'n_estimators': [100, 200, 300], 'max_depth': [5, 10, 15, None]} 
grid_search = GridSearchCV(rf, param_grid, cv=5)
grid_search.fit(X_train, y_train)

y_pred_rf = grid_search.predict(X_test)
rf_residuals = np.square(y_pred_rf - y_test)

# Height Formula based Model
y_pred_ht = X_test["ht"]/10 + 5
ht_residuals = np.square(y_pred_ht - y_test)

# Paired t-test
t_test_results = stats.ttest_rel(rf_residuals, ht_residuals)

df1 = pd.DataFrame({
    "Model": ["Random Forest", "Height-based Formula"],
    "Residuals Mean Squared Error": [np.mean(rf_residuals), np.mean(ht_residuals)],
    "T-statistic": [t_test_results.statistic, t_test_results.statistic],
    "P-value": [t_test_results.pvalue, t_test_results.pvalue]},
    index=['1', '2']
)

df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0], 
    'Random Forest: Best parameters': grid_search.best_params_,
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
