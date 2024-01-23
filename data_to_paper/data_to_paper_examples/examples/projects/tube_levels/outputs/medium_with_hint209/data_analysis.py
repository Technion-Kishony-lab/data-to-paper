
# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import mean_squared_error
import pickle
from scipy import stats

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of age and height stratified by sex"
df0 = df.groupby("sex")[["age_c", "ht", "wt", "tube_depth_G"]].describe().stack()
df0.index.rename(names=['gender', 'statistic'], inplace=True)
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
#No preprocessing is needed, because all numerical variables are already standardized and sex is binary.

# ANALYSIS
# Dividing data into train and test sets
X = df[['sex', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

# Table 1: "Machine-Learning Model: Random Forest Regression Predicting OTTD"
rf_regressor = RandomForestRegressor(random_state=0)
param_grid = {
   'n_estimators': [50, 100],
   'max_depth': [10, 20],
   'min_samples_split': [2],
   'min_samples_leaf': [1, 2]
}

grid_search_rf = GridSearchCV(rf_regressor, param_grid=param_grid, cv=3)
grid_search_rf.fit(X_train, y_train)
df1 = pd.DataFrame({'Best parameters of RF model': [str(grid_search_rf.best_params_)]}, index=["ML Model"])
df1.to_pickle('table_1.pkl')

# Table 2: "Formula-Based Model: Prediction Based on Height Formula"
predicted_OTTD_height = X_test['ht'] / 10 + 5
df2 = pd.DataFrame({'intercept': [5], 'coefficient of height': [0.1]}, index=["Formula"])
df2.to_pickle('table_2.pkl')

# Table 3: "Hypothesis Testing: Comparing The Mean Squared Residuals of RF model and Formula-Based Model"
# Calculate predictions and residuals for the RF model
y_pred_rf = grid_search_rf.predict(X_test)
residuals_rf = (y_pred_rf - y_test)**2
# Calculate residuals for the formula-based model
residuals_height = (predicted_OTTD_height - y_test)**2
# Perform a paired t-test 
t_test_results = stats.ttest_rel(residuals_rf, residuals_height)
df3 = pd.DataFrame({
   "mean_squared_residuals": [residuals_rf.mean(), residuals_height.mean()],
   "std_squared_residuals": [residuals_rf.std(), residuals_height.std()],
   "t_stat": [t_test_results.statistic]*2,
   "p_val": [t_test_results.pvalue]*2
   }, index=["RF Model", "Formula-Based Model"])
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': str(len(df)),
 'MSE of RF model': str(mean_squared_error(y_test, y_pred_rf)),
 'MSE of Formula-Based model': str(mean_squared_error(y_test, predicted_OTTD_height)),
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
