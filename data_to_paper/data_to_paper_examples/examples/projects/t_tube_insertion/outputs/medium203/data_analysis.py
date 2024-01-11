

# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from scipy import stats
from sklearn.metrics import mean_squared_error
import pickle

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# no dataset preparations are needed

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of height and age stratified by sex"
grouped = data.groupby("sex").agg({"ht": ["mean", "std"], "age_c": ["mean", "std"]})
df0 = grouped.rename(index={0:'female', 1: 'male'})
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed, because all the data are in final form and we do not need to transform any categorical variables

# ANALYSIS
# Table 1: Comparison of residuals for two models – formula-based and Random Forest
y = data['tube_depth_G']

# Preparing X Data
X = data[['sex', 'age_c', 'ht', 'wt']]

# Preparing X_train and X_test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Random Forest model
rf = RandomForestRegressor(n_estimators=100, max_depth=7)
rf.fit(X_train, y_train)
rf_predicted = rf.predict(X_test)

# Compute residuals for the RF model
rf_residuals = np.square(y_test - rf_predicted)

# Formula-based model
formula_predicted = X_test['ht'] / 10 + 5
# Compute residuals for the formula-based model
formula_residuals = np.square(y_test - formula_predicted)

# Paired t-test of the residuals
paired_t_test = stats.ttest_rel(rf_residuals, formula_residuals)

# Create dataframe
df1 = pd.DataFrame({
 'Model': ['Random Forest', 'Formula-based Model'],
 'Mean of Squared Residuals': [rf_residuals.mean(), formula_residuals.mean()],
 'Paired t-test p value': [paired_t_test.pvalue, paired_t_test.pvalue]
}, index=['Model 1', 'Model 2'])

df1.to_pickle('table_1.pkl')


# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data),
 'Accuracy of Random Forest Regression model': rf.score(X_test, y_test),
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
