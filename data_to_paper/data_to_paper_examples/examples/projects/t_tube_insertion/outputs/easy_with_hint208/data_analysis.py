

# IMPORT
import pandas as pd
import numpy as np
import scipy 
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from scipy.stats import ttest_rel, wilcoxon
import pickle

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed. The data is already clean.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of height and age stratified by sex"
df0 = data.groupby('sex')[['ht', 'age_c']].agg(['mean', 'std']).round(2)
df0.index = df0.index.map({0: "0-Female", 1: "1-Male"})
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# Create dummy variables for categorical variable 'sex'
data = pd.get_dummies(data, columns=['sex'], drop_first=True)

# Standardize values of continuous features and create new columns for them
scaler = StandardScaler()
scaled_features = scaler.fit_transform(data[['tube', 'age_c', 'ht', 'wt']])
data[['tube_s', 'age_c_s', 'ht_s', 'wt_s']] = pd.DataFrame(scaled_features, columns=['tube_s', 'age_c_s', 'ht_s', 'wt_s'])

# ANALYSIS
# Split the data into training and testing sets
X = data.drop(['tube_depth_G', 'tube'], axis=1)
y = data['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Train RandomForest with hyperparameter tuning
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [None, 10],
    'min_samples_split': [2, 5]
}
rf = RandomForestRegressor()
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5)
grid_search.fit(X_train, y_train)

# Train ElasticNet
en = ElasticNetCV()
en.fit(X_train, y_train)

# Get predictions
rf_pred = grid_search.predict(X_test)
en_pred = en.predict(X_test)

# Calculate squared residuals
rf_residual = (rf_pred - y_test) ** 2
en_residual = (en_pred - y_test) ** 2

# Perform Paired t-test
t_test = ttest_rel(rf_residual, en_residual)

## Table 1: "Comparison of squared residuals from Random Forest and Elastic Net models"
df1 = pd.DataFrame({'RandomForest_mean_residual': [rf_residual.mean()],
                    'RandomForest_std_residual': [rf_residual.std()],
                    'ElasticNet_mean_residual': [en_residual.mean()],
                    'ElasticNet_std_residual': [en_residual.std()],
                    't-statistic': [t_test.statistic],
                    'p-value': [t_test.pvalue]}, index=["Result"]).round(2)
df1.to_pickle('table_1.pkl')

# Perform Wilcoxon signed-rank test
wilcoxon_test = wilcoxon(rf_residual - en_residual)

## Table 2: "Wilcoxon signed-rank test on squared residuals from Random Forest and Elastic Net models"
df2 = pd.DataFrame({'z-statistic': [wilcoxon_test.statistic], 'p-value': [wilcoxon_test.pvalue]}, index=["Result"]).round(2)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data), 
    'Random Forest Score': grid_search.score(X_test, y_test),
    'Random Forest Best Parameters': grid_search.best_params_,
    'Elastic Net Score': en.score(X_test, y_test)
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
