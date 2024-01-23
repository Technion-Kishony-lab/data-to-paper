
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from scipy import stats
import pickle

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of height and age stratified by sex"
df0 = df.groupby("sex").agg(["mean", "std"])[["ht", "age_c"]]
df0.index = ['female', 'male']
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# The variables are already in a format suitable for regression.

# ANALYSIS

# ML Model: Random Forest
# Split data into features and target
X = df[["sex", "age_c","ht","wt"]]
y = df["tube_depth_G"]

# Split dataset into train and test data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1)

# Create RF regressor object and train on the data
RF = RandomForestRegressor(n_estimators=500, random_state=1)
RF.fit(X_train, y_train)

# Predict on the test data and save predictions for comparison
rf_predictions = RF.predict(X_test)

# Calculation of errors for ML model
rf_errors = (y_test - rf_predictions) ** 2

# Formula-Based Model: height [cm] / 10 + 5 cm
formula_predictions = X_test["ht"] / 10 + 5

# Calculation of errors for Formula model
formula_errors = (y_test - formula_predictions) ** 2

# Perform paired t-test between the squared errors
ttest_results = stats.ttest_rel(rf_errors, formula_errors)

# Create dataframe for results
df1 = pd.DataFrame({
    'Model': ['Random Forest', 'Height Formula'],
    'Mean Squared Error': [np.mean(rf_errors), np.mean(formula_errors)],
    'T-Test Statistic': [ttest_results.statistic, '-'],
    'P-value': [ttest_results.pvalue, '-'],
    })
df1.set_index("Model", inplace=True)

# Save the dataframe for the scientific table
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
 'R_squared of Random Forest model': r2_score(y_test, rf_predictions),
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
