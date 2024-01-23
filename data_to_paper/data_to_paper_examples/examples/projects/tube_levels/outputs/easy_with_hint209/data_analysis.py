
# IMPORT
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed.

# ANALYSIS
# The analysis will comprise the construction of Random Forest and Elastic Net models,
# hyperparameter tuning, calculation of the mean squared residuals of the models, and 
# comparative testing of the models using a paired t-test.

# Prepare data for model training
features = df[['sex', 'age_c', 'ht', 'wt']]
target = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=0)

## Table 1: "Performance of the Random Forest Model"
# Construct and tune the Random Forest model
rf = RandomForestRegressor()
rf_params = {'n_estimators': [50, 100, 200], 'max_depth': [None, 5, 10], 'min_samples_split': [2, 5, 10]}
rf_grid = GridSearchCV(rf, rf_params, cv=5)
rf_grid.fit(X_train, y_train)

# Predict and calculate the mean squared residuals
rf_preds = rf_grid.predict(X_test)
rf_errors = (rf_preds - y_test) ** 2
mean_rf_error = rf_errors.mean()
df1 = pd.DataFrame({'Model': ['Random Forest'], 'Mean Squared Residual': [mean_rf_error]}, index=['RF'])
df1.to_pickle('table_1.pkl')

## Table 2: "Performance of the Elastic Net Model"
# Construct and tune the Elastic Net model
en = ElasticNet()
en_params = {'alpha': [0.1, 0.5, 1.0, 2.0], 'l1_ratio': [0.2, 0.5, 0.8]}
en_grid = GridSearchCV(en, en_params, cv=5)
en_grid.fit(X_train, y_train)

# Predict and calculate the mean squared residuals
en_preds = en_grid.predict(X_test)
en_errors = (en_preds - y_test) ** 2
mean_en_error = en_errors.mean()
df2 = pd.DataFrame({'Model': ['Elastic Net'], 'Mean Squared Residual': [mean_en_error]}, index=['EN'])
df2.to_pickle('table_2.pkl')

## Table 3: "Comparative Performance of the Random Forest and Elastic Net Models"
# Compare the performance of the two models using a paired t-test
ttest_results = ttest_rel(rf_errors, en_errors)
df3 = pd.DataFrame({'Model Pair': ['RF vs EN'], 't-statistic': [ttest_results.statistic], 'p-value': [ttest_results.pvalue]}, index=['Comparison'])
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Number of Observations': len(df),
 'Best Parameters for RF': rf_grid.best_params_,
 'Best Parameters for EN': en_grid.best_params_,
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
