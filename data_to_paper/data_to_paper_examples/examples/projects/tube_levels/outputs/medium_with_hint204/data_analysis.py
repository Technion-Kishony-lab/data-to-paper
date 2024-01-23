
# IMPORT
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from scipy import stats
import pickle
import numpy as np

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## No descriptive statistics table is created, because characteristics of the data have been described in dataset output.

# PREPROCESSING 
# No preprocessing is needed, because our data is already in numerical format.

# ANALYSIS
## Table 1: "Comparison of predictive powers of RF Machine Learning Model and Height-Formula Based Model"

# Split data into training and test sets
train, test = train_test_split(df, test_size=0.2, random_state=42)

# Train RF model
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(train[['sex', 'age_c', 'ht', 'wt']], train['tube_depth_G'])

# Predict using RF model
test['rf_predictions'] = rf.predict(test[['sex', 'age_c', 'ht', 'wt']])

# Predict using Height-Formula based model
test['formula_predictions'] = test['ht'] / 10 + 5

# Calculate squared residuals for each model
test['rf_squared_residuals'] = (test['tube_depth_G'] - test['rf_predictions']) ** 2
test['formula_squared_residuals'] = (test['tube_depth_G'] - test['formula_predictions']) ** 2

# Carry out paired t-test
ttest_results = stats.ttest_rel(test['rf_squared_residuals'], test['formula_squared_residuals'])

df1 = pd.DataFrame({
    'model': ['RF Machine Learning Model', 'Height-Formula Based Model'],
    'mean_squared_residuals': [test['rf_squared_residuals'].mean(), test['formula_squared_residuals'].mean()],
    'std_dev_squared_residuals': [test['rf_squared_residuals'].std(), test['formula_squared_residuals'].std()]
})
df1['95% CI_squared_residuals'] = df1.apply(lambda row: stats.norm.interval(0.95, 
                                                                            loc=row['mean_squared_residuals'], 
                                                                            scale=row['std_dev_squared_residuals']/np.sqrt(len(test))), axis=1)

df1['p_value'] = ttest_results.pvalue
df1.set_index('model', inplace=True)
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
 'Accuracy of RF regression model': rf.score(test[['sex', 'age_c', 'ht', 'wt']], test['tube_depth_G'])
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
