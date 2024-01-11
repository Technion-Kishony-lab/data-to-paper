
# IMPORT
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV
from scipy import stats
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS

# No dataset preparations are needed

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of age, height, weight, and OTTD stratified by sex"
df0 = data.groupby('sex').agg({'age_c': ['mean', 'std'], 'ht': ['mean', 'std'], 'wt': ['mean', 'std'], 'tube_depth_G': ['mean', 'std']})
df0.index = ['Female', 'Male']   
df0.columns = ['_'.join(col).strip() for col in df0.columns.values]
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed, because the data are already in suitable format for machine learning.

# ANALYSIS
features = ['sex', 'age_c', 'ht', 'wt']
target = 'tube_depth_G'
X = data[features]
y = data[target]

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Train and predict with Random Forest
rf = RandomForestRegressor()
rf.fit(X_train, y_train)
rf_y_pred = rf.predict(X_test)

# Train and predict with Elastic Net
en = ElasticNetCV()
en.fit(X_train, y_train)
en_y_pred = en.predict(X_test)

# Calculate squared residuals
rf_squared_residuals = (rf_y_pred - y_test)**2
en_squared_residuals = (en_y_pred - y_test)**2

## Table 1: "Comparison of predictive power between Random Forest and Elastic Net models"
t_test_results = stats.ttest_rel(rf_squared_residuals, en_squared_residuals)

df1 = pd.DataFrame({
    'Mean Squared Residual': [np.mean(rf_squared_residuals), np.mean(en_squared_residuals)],
    'P-value': [t_test_results.pvalue, '-']
}, index=['Random Forest', 'Elastic Net'])
df1.to_pickle('table_1.pkl')

model = smf.ols(formula='tube_depth_G ~ sex + age_c + ht + wt', data=data)
results = model.fit()

## Table 2: "Association of age, sex, height, and weight with OTTD"
df2 = pd.DataFrame({
    'Coefficient': results.params,
    'P-value': results.pvalues
}, index=['Intercept', 'sex', 'age_c', 'ht', 'wt'])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data),
 'Root Mean Square Error of Random Forest': np.sqrt(mean_squared_error(y_test, rf_y_pred)),
 'Root Mean Square Error of Elastic Net': np.sqrt(mean_squared_error(y_test, en_y_pred)),
 'R-squared of Multiple linear regression': results.rsquared
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
