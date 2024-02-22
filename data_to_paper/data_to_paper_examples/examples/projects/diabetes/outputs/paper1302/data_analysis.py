
# IMPORT
import pandas as pd
import numpy as np
import pickle
import statsmodels.formula.api as smf

# LOAD DATA
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of main binary variables and BMI stratified by sex"
df_sex = df.groupby('Sex').agg(
{'Diabetes_binary': ['mean','std'],
'PhysActivity': ['mean','std'],
'BMI': ['mean', 'std']}).reset_index()

df_sex.columns = ['Sex', 'Mean Diabetes', 'Std Diabetes', 'Mean PhysActivity', 'Std PhysActivity', 'Mean BMI', 'Std BMI']
df_sex.Sex = df_sex.Sex.replace({0: 'Female', 1: 'Male'})
df_sex.set_index('Sex', inplace=True)  # setting Sex as the index, for better row labels
df_sex.to_pickle('table_0.pkl')

# PREPROCESSING 
# Creating dummy variables for categorical variables.
df = pd.get_dummies(df, columns=['Sex', 'Age', 'Education', 'Income'])

# ANALYSIS
## Table 1: "Results of Multiple Linear Regression testing association between physical activity level and diabetes, adjusting by age, sex, and BMI"
formula = 'Diabetes_binary ~ PhysActivity + BMI + Sex_1'
model = smf.ols(formula, data=df)
res = model.fit()
df1 = pd.DataFrame({
'coef': res.params, 
'p-value': res.pvalues, 
'conf_int_low': res.conf_int().iloc[:, 0],
'conf_int_high': res.conf_int().iloc[:, 1]
})
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
'Total number of observations': df.shape[0],
'R-squared of the model': res.rsquared,
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

