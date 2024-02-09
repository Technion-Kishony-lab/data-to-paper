

# IMPORT
import pandas as pd
import numpy as np
import statsmodels.api as sm
import pickle

# LOAD DATA
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed. The dataset is already clean 

# DESCRIPTIVE STATISTICS
# Table 0: "Prevalence of Diabetes in relation to Fruits and Veggies consumption"
grouped = df.groupby(['Fruits', 'Veggies', 'Diabetes_binary']).size().reset_index(name='Counts')
df0 = grouped.pivot_table(index=['Fruits', 'Veggies'], 
                          columns='Diabetes_binary', 
                          values='Counts').reset_index().fillna(0)
df0.columns = ['Fruits', 'Veggies', 'Non-Diabetics', 'Diabetics']
df0.index = ['Row'+str(i) for i in range(1, len(df0)+1)]
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because all variables are binary or in appropriate ordinal scale for this analysis.

# ANALYSIS

## Table 1: "Multiple Logistic Regression Model predicting Diabetes with Fruit, Veggies consumption and controlling for BMI and Age"
X = df[['Fruits', 'Veggies', 'BMI', 'Age']]
X = sm.add_constant(X)
Y = df['Diabetes_binary']

model = sm.Logit(Y, X)
result = model.fit()
summary = result.summary2()
coeffs = summary.tables[1]

df1 = coeffs[['Coef.', 'Std.Err.', 'P>|z|']].rename(columns={"Coef.": "Coefficient", "Std.Err.": "Standard Error", "P>|z|": "p-value"})

df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS

additional_results = {
 'Total number of observations': df.shape[0],  
 'Log-Likelihood of regression model': result.llf,
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
