
# IMPORT
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed, data is already clean.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# No preprocessing is needed because all data has been preprocessed in the dataset preparation step.

# ANALYSIS

## Table 1: "Association between fruit and vegetable consumption and risk of diabetes"
# Run logistic regression model adjusting for confounding variables
model = smf.logit('Diabetes_binary ~ Fruits + Veggies + Age + Sex + Education + Income', data=df)
result = model.fit()
df1 = pd.DataFrame(result.summary2().tables[1])
df1.to_pickle('table_1.pkl')

## Table 2: "Income level as a moderator in the relationship between fruit and vegetable consumption and risk of diabetes"
# Run logistic regression model adjusting for confounders and including interaction between dietary habits and income
model = smf.logit('Diabetes_binary ~ Fruits + Veggies + Income + Fruits:Income + Veggies:Income + Age + Sex + Education', data=df)
result = model.fit()
df2 = pd.DataFrame(result.summary2().tables[1])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0],
    'Percentage of diabetes patients': df.Diabetes_binary.mean() * 100,
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
