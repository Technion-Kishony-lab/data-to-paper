
# IMPORT
import pandas as pd
import numpy as np
import statsmodels.formula.api as sm
import pickle

# LOAD DATA
data = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of key variables"
key_vars = ['Diabetes_binary', 'BMI', 'PhysActivity', 'Smoker', 'Fruits', 'Veggies']
df0 = data[key_vars].describe().transpose()  # generates descriptive statistics
df0 = df0[['count', 'mean', 'std']]  # keeps only count, mean, and std
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because the dataset is already properly formatted.

# ANALYSIS
## Table 1: "Analysis of relationship between BMI and Diabetes moderated by Physical Activity"
model = sm.ols(formula="Diabetes_binary ~ BMI*PhysActivity + Age + Sex + Education + Income", data=data)
results = model.fit()
df1 = pd.DataFrame(results.summary2().tables[1])  # outputs in DataFrame
df1.to_pickle('table_1.pkl')

## Table 2: "Analysis of relationship between BMI and Diabetes moderated by Smoking"
model = sm.ols(formula="Diabetes_binary ~ BMI*Smoker + Age + Sex + Education + Income", data=data)
results = model.fit()
df2 = pd.DataFrame(results.summary2().tables[1])  # outputs in DataFrame
df2.to_pickle('table_2.pkl')

## Table 3: "Analysis of relationship between BMI and Diabetes moderated by Consumption of Fruits and Vegetables"
model = sm.ols(formula="Diabetes_binary ~ BMI*Fruits + BMI*Veggies + Age + Sex + Education + Income", data=data)
results = model.fit()
df3 = pd.DataFrame(results.summary2().tables[1])  # Outputs in DataFrame
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data),         
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
