

# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error
from scipy import stats
import pickle
import warnings

# LOAD DATA
df_original = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 

# Dummifying categorical variable 'sex' for modeling
df_original = pd.get_dummies(df_original, columns=['sex'], drop_first=True)

# ANALYSIS

# ========= RF Model =========
# Preparing target and feature sets for training
X = df_original[['sex_1', 'age_c', 'ht', 'wt']]
y = df_original['tube_depth_G']

# Splitting the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

# Instantiate the RF model
rf = RandomForestRegressor(random_state = 42)

# Set up parameter grid for tuning
param_grid_rf = { 
    "n_estimators" : [10, 50, 100],
    "max_features" : ['sqrt', 'log2']
    }

# Build GridSearch
CV_rf = GridSearchCV(estimator=rf, param_grid=param_grid_rf, cv= 5)
CV_rf.fit(X_train, y_train)

# Predict OTTD with the tuned RF model
rf_pred = CV_rf.predict(X_test)
rf_mse = mean_squared_error(y_test,rf_pred)

# ========= EN Model =========
# Instantiate the EN model
en = ElasticNet(random_state=42)

# Set up hyperparameter grid for tuning
param_grid_en = {
    "alpha": [0.1, 0.5, 1],
    "l1_ratio": [0.1, 0.3, 0.5, 0.7, 0.9]
    }

# Build GridSearch
CV_en = GridSearchCV(estimator=en, param_grid=param_grid_en, cv= 5)
CV_en.fit(X_train, y_train)

# Predict OTTD with the tuned EN model
en_pred = CV_en.predict(X_test)
en_mse = mean_squared_error(y_test,en_pred)

# Build dataframes for the scientific tables

# Table 1: Mean squared residuals of both models
df1 = pd.DataFrame(
    {"RF_model": [rf_mse],
     "EN_model": [en_mse]},
     index=["Mean_squared_residuals"])

df1.to_pickle('table_1.pkl')

# Use paired t-test to compare the mean squared residuals of RF and EN models
ttest_results = stats.ttest_rel(rf_pred, en_pred)

# Table 2: Test results of comparing the predictive power of RF and EN models
df2 = pd.DataFrame({
    "t_statistic": [ttest_results.statistic],
    "p_value": [ttest_results.pvalue]},
    index=["Paired_t_test"])

df2.to_pickle('table_2.pkl')
        
# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df_original.shape[0], 
 'RF_model_tuned_parameters': CV_rf.best_params_,
 'EN_model_tuned_parameters': CV_en.best_params_
}

# Save additional results
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
