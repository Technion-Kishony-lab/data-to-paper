
# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import mean_squared_error
from scipy import stats
import pickle

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of patient ages and weights stratified by their sex"
df0_mean = data.groupby('sex')[['age_c', 'wt']].mean()
df0_std = data.groupby('sex')[['age_c', 'wt']].std()
df0 = pd.concat([df0_mean, df0_std], axis=1)
df0.columns = ["average_age", "average_weight", "standard_deviation_age", "standard_deviation_weight"]
df0.index = df0.index.map({0: 'female', 1: 'male'})  # 'sex' column will be used as the index
df0.to_pickle('table_0.pkl') 

# PREPROCESSING
# No preprocessing is needed because data doesn't have any categorical variables
# and is already in a format suitable for machine learning model

# ANALYSIS 
# Table 1: "Predictive Power of Machine Learning Models"

# First split the data into train and validation sets
X = data[['sex', 'age_c', 'ht', 'wt']]
y = data['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize models
rf = RandomForestRegressor(random_state = 42)
en = ElasticNet(random_state = 42)

# Define parameters for grid search
params_rf = {'n_estimators': np.arange(10, 100, 10)}
params_en = {'alpha': [0.2, 0.4, 0.6, 0.8, 1], 'l1_ratio': [0.1, 0.5, 0.9]}   # Reduced parameters for ElasticNet

# Grid search over parameters
grid_rf = GridSearchCV(estimator=rf, param_grid=params_rf, cv=5)
grid_en = GridSearchCV(estimator=en, param_grid=params_en, cv=5)

# Fit models
grid_rf.fit(X_train, y_train)
grid_en.fit(X_train, y_train)

# Get predictions
rf_preds = grid_rf.predict(X_test)
en_preds = grid_en.predict(X_test)

#Perform paired t-test, keeping results object
ttest_results = stats.ttest_rel(rf_preds, en_preds)

# Create dataframe for the table
df1 = pd.DataFrame({
    'model': ['Random Forest', 'Elastic Net'],
    'R2_score': [grid_rf.score(X_test, y_test), grid_en.score(X_test, y_test)],
    'RMSE': [np.sqrt(mean_squared_error(y_test, rf_preds)), np.sqrt(mean_squared_error(y_test, en_preds))],
    't-statistic': [ttest_results.statistic, '-'],
    'p-value': [ttest_results.pvalue, '-']
})

df1.set_index('model', inplace=True)  # setting 'model' column as the index
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data),
 'best parameters for RF': grid_rf.best_params_,
 'best parameters for EN': grid_en.best_params_
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
