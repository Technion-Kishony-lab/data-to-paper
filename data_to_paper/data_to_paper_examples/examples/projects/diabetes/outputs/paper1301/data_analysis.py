
# IMPORT
import pandas as pd
import numpy as np
import pickle
import statsmodels.formula.api as smf

# LOAD DATA
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed as there are no missing values.
# Nor does the dataset require any aggregated operations or dataset joining operations.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of Physical Activity stratified by Diabetes"
df0 = df.groupby('Diabetes_binary')['PhysActivity'].agg(['mean', 'std'])
df0.index = ['No Diabetes', 'Diabetes']
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed as data is already cleaned. All variables are either binary or ordinal and there're no categorical variables that require dummy variables.
# The numerical features do not require normalization or standardization as they will be fed to a logistic regression model that is agnostic to the scale of the features.

# ANALYSIS
## Table 1: "Association between physical activity and diabetes prevalence"
formula = "Diabetes_binary ~ PhysActivity + Age + BMI + Smoker + HighBP + HighChol + Education + Income"
model1 = smf.logit(formula, data=df).fit()
df1 = model1.summary2().tables[1]
df1.to_pickle('table_1.pkl')

## Table 2: "Moderating effect of BMI on the association between physical activity and diabetes prevalence"
formula = "Diabetes_binary ~ PhysActivity*BMI + Age + BMI + Smoker + HighBP + HighChol + Education + Income"
model2 = smf.logit(formula, data=df).fit()
df2 = model2.summary2().tables[1] 
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
 'Pseudo R-squ of model1': model1.prsquared,
 'Pseudo R-squ of model2': model2.prsquared,
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
