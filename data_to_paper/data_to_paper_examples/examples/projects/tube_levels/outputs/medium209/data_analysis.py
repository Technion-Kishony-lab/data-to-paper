
# IMPORT
import pickle
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# No preprocessing is needed.

# ANALYSIS
## Table 1: "Comparison of predictive performance of machine-learning model and formula-based model"

# Split the data into independent and dependent variables
X = df[['sex', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']

# Split the data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state = 42)

# Initialize the Random Forest regressor
rf = RandomForestRegressor(random_state=42)

# Fit the model to the training data
rf.fit(X_train, y_train)

# Predict OTTD using the RF model and calculate Mean Squared Error (MSE)
rf_pred = rf.predict(X_test)
rf_mse = mean_squared_error(y_test, rf_pred)

# Predict OTTD using the height formula and calculate MSE
formula_pred = X_test['ht'] / 10 + 5
formula_mse = mean_squared_error(y_test, formula_pred)

# Perform paired t-test and get the results
ttest_results = stats.ttest_rel(rf_pred, formula_pred)

# Create a dataframe for a scientific table
df1 = pd.DataFrame({
    'Model': ['RF Model', 'Formula-Based Model'],
    'MSE': [rf_mse, formula_mse],
    'p-value': [ttest_results.pvalue, ttest_results.pvalue]
}).set_index('Model')
df1.index.name = None
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    't_statistic': ttest_results.statistic,
    'p_value': ttest_results.pvalue
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
