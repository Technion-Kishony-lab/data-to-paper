
# IMPORT
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of height and age stratified by sex"
df0 = df.groupby('sex').agg({'age_c': ['mean', 'std'], 'ht':['mean', 'std']})
df0.index = ['Female', 'Male']
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because the data is ready for analysis.
  
# ANALYSIS
## Table 1: "Comparison of Random Forest model with Formula-based model for predicting OTTD"
# Train-Test split on original dataset
X_train, X_test, y_train, y_test = train_test_split(df[['sex', 'age_c', 'ht', 'wt']], df['tube_depth_G'], test_size=0.3, random_state=42)

# ML MODEL
rf = RandomForestRegressor(n_estimators=500, max_depth=10, random_state=42)
rf.fit(X_train, y_train)
predictions_rf = rf.predict(X_test)
residuals_rf = (y_test - predictions_rf)**2

# FORMULA-BASED MODEL
predictions_formula = (X_test['ht']/10) + 5
residuals_formula = (y_test - predictions_formula)**2

# Perform paired t-test on the squared residuals of the two models
p_value = ttest_rel(residuals_rf, residuals_formula).pvalue

# Create dataframe for Table 1
df1 = pd.DataFrame({'Model': ['Random Forest', 'Height-based model'],
                    'Average Squared Residual': [residuals_rf.mean(), residuals_formula.mean()],
                    'p-value': [p_value, p_value]})
df1.set_index('Model', inplace=True)

df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {'Total number of observations': df.shape[0],
                      'Mean Absolute Error of RF model': np.mean(np.abs(y_test - predictions_rf)),
                      'Mean Absolute Error of Height-based model': np.mean(np.abs(y_test - predictions_formula))}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
