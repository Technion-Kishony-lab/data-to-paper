
# IMPORT
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GridSearchCV
import pickle
from scipy.stats import ttest_rel


# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")


# DATASET PREPARATIONS
# No dataset preparations are needed.


# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.


# PREPROCESSING 
# No preprocessing is needed.


# ANALYSIS
## Table 1: "Mean squared errors of ML model and formula-based model, and p-value from paired t-test"
# Separate the target and predictor variables
X = df[['sex', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']

# Split the data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Hyperparameter tuning for Random Forest model
param_grid = {'n_estimators': [50, 100, 200], 'max_depth': [None, 5, 10, 15, 20]}
rf = RandomForestRegressor(random_state = 42)
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5)
grid_search.fit(X_train, y_train)
rf_best = grid_search.best_estimator_

# Compute the prediction for Random Forest model
rf_predictions = rf_best.predict(X_test)

# Compute the prediction for formula-based model
formula_predictions = (X_test['ht'] / 10 + 5)

# Create dataframe for residuals and perform paired t-test
df_mse = pd.DataFrame()
df_mse['ML_model_MSE'] = [mean_squared_error(y_test, rf_predictions)]
df_mse['formula_model_MSE'] = [mean_squared_error(y_test, formula_predictions)]
df_mse.set_index(pd.Index(['Mean Squared Error']), inplace=True)

# Calculating residuals for paired t-test
rf_residuals = y_test - rf_predictions
formula_residuals = y_test - formula_predictions

# Paired t-test on residuals
ttest_result = ttest_rel(rf_residuals, formula_residuals)
df_mse['Paired_ttest_pval'] = [ttest_result.pvalue]

# Save MSE table
df_mse.to_pickle('table_1.pkl')


# SAVE ADDITIONAL RESULTS
additional_results = {
 'Best parameters for Random Forest': grid_search.best_params_, 
}
# Save additional results
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
