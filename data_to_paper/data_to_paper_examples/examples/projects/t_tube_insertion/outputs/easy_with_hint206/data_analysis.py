
# IMPORT
import pickle
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# Standardizing numeric features
scaler = StandardScaler()
df[['age_c_scaled', 'ht_scaled', 'wt_scaled']] = scaler.fit_transform(df[['age_c', 'ht', 'wt']])

# Splitting the dataset into training and test sets
X_train, X_test, y_train, y_test = train_test_split(
    df[['sex', 'age_c_scaled', 'ht_scaled', 'wt_scaled']],
    df['tube_depth_G'],
    test_size=0.3,
    random_state=1
)

# ANALYSIS
## Table 1: "Comparison of Mean Squared Errors of the Models"
# Fit Random Forest (RF) model with hyperparameter tuning
rf = RandomForestRegressor(random_state=1)
param_grid = {
    'n_estimators': [int(x) for x in np.linspace(start=10, stop=100, num=3)],
    'max_depth': [int(x) for x in np.linspace(10, 50, num=3)],
    'min_samples_split': [2, 5]
}
rf_search = RandomizedSearchCV(estimator=rf, param_distributions=param_grid, n_iter=10, cv=3, n_jobs=-1, random_state=1)
rf_search.fit(X_train, y_train)

# Predict and calculate squared residuals
rf_residuals = (rf_search.predict(X_test) - y_test)**2

# Fit Elastic Net (EN) model
en = ElasticNetCV(random_state=1)
en.fit(X_train, y_train)

# Predict and calculate squared residuals
en_residuals = (en.predict(X_test) - y_test)**2

# Perform t-test on the residuals
res = stats.ttest_rel(rf_residuals, en_residuals)

# Create dataframe for Table 1
df1 = pd.DataFrame({
    'Model': ['Random Forest', 'Elastic Net'],
    'Mean Squared Error': [np.mean(rf_residuals), np.mean(en_residuals)],
    't-value': [res.statistic, res.statistic],
    'p-value': [res.pvalue, res.pvalue]
}, index=['Model 1', 'Model 2'])
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0],
    'accuracy of Random Forest model': rf_search.score(X_test, y_test),
    'accuracy of Elastic Net model': en.score(X_test, y_test)
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
