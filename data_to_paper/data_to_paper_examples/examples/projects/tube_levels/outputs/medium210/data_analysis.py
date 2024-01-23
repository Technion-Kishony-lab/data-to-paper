
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of Optimal Tracheal Tube Depth (OTTD) stratified by sex"
df0 = data.groupby('sex')['tube_depth_G'].agg(['mean', 'std'])
df0.index = ['female', 'male']  # Changing index to meaningful labels
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because all our necessary features are numerical.
# Creating the formula-based column
data['predicted_formula'] = data['ht'] / 10 + 5

# ANALYSIS 
## Table 1: "Predictive performance of the machine-learning model vs the formula-based model"
# Splitting the data
train, test = train_test_split(data, test_size=0.2, random_state=42)

# Define features and target
features = ['sex', 'age_c', 'ht', 'wt']
target = 'tube_depth_G'

# Training the model
rf_reg = RandomForestRegressor(max_depth=5, random_state=0)
rf_reg.fit(train[features], train[target])

# Making predictions
test['predicted_ML'] = rf_reg.predict(test[features])

# Calculate squared residuals
test['residuals_ML'] = (test[target] - test['predicted_ML']) ** 2
test['residuals_formula'] = (test[target] - test['predicted_formula']) ** 2

# Table 1
table_1_cols = ['predicted_ML', 'predicted_formula', 'residuals_ML', 'residuals_formula']
df1 = test[table_1_cols].agg(['mean', 'std'])

df1.to_pickle('table_1.pkl')

## Hypothesis test
ttest_result = ttest_rel(test['residuals_ML'], test['residuals_formula'])

# Raise an error if our ML model does not have a significantly better predictive performance than the formula-based model
assert ttest_result.pvalue < 0.05, "The machine-learning model does not have a significantly better predictive performance than the formula-based model"

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data), 
 'T statistic': ttest_result.statistic, 
 'P value': ttest_result.pvalue,
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
