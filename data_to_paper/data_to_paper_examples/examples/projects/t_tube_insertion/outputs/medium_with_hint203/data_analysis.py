
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
import pickle

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed

# PREPROCESSING
# No preprocessing is needed, because all necessary data are numeric and no missing values are observed.

# ANALYSIS

## Table 1: "Summary statistics for observed and predicted OTTDs with height formula-based model"
# Calculate predicted OTTD using height formula
data['predicted_formula'] = data['ht']/10 + 5 
data['residual_formula'] = data['predicted_formula'] - data['tube_depth_G']
# summarize the predicted and actual values.
summary_predicted = data[['tube_depth_G', 'predicted_formula']].agg(['mean', 'std'])
summary_residuals = data['residual_formula'].agg(['mean', 'std'])
df1 = pd.concat([summary_predicted, summary_residuals], axis=1)
df1.to_pickle('table_1.pkl')

## Table 2: "Optimal parameters and performance of the Random Forest model"
# Prepare data for the RF model
features = ['sex', 'age_c', 'ht', 'wt']
X = data[features]
y = data['tube_depth_G']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

# Set array of possible parameter values for the RF model
params = {'n_estimators': [50, 100, 200], 'max_depth': [None, 5, 10]}

# Hyper-parameter tuning for the RF model
rf_regressor = GridSearchCV(RandomForestRegressor(random_state=0), params, cv=5, scoring='neg_mean_squared_error')
rf_regressor.fit(X_train, y_train)

#RUN the RF model
rf = RandomForestRegressor(n_estimators=rf_regressor.best_params_['n_estimators'], max_depth=rf_regressor.best_params_['max_depth'])
rf.fit(X_train, y_train)

# Create DataFrame for Table 2
df2 = pd.DataFrame({'best_param_n_estimators': [rf_regressor.best_params_['n_estimators']],
                    'best_param_max_depth': [rf_regressor.best_params_['max_depth']],
                    'best_score': [(-1) * rf_regressor.best_score_]})
df2.index = ['RF_model']
df2.to_pickle('table_2.pkl')

## Table 3: "Paired t-test between the squared residuals of the machine-learning model and the formula-based model"
# Calculate predicted OTTD with the RF model
data['predicted_rf'] = rf.predict(X)
data['residual_rf'] = data['predicted_rf'] - data['tube_depth_G']

# calculate square of residuals
data['residual_squared_formula'] = np.square(data['residual_formula'])
data['residual_squared_rf'] = np.square(data['residual_rf'])

# Run paired t-test
t_test_results = stats.ttest_rel(data['residual_squared_formula'], data['residual_squared_rf'])

# Create DataFrame for Table 3
df3 = pd.DataFrame({'t_stat': [t_test_results.statistic], 'pvalue': [t_test_results.pvalue]}, index=['rf_vs_formula'])
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data),
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
