
# IMPORT
import pandas as pd
import numpy as np
import pickle
import statsmodels.api as sm

# LOAD DATA
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Mean and STD of physical activity, BMI, age and sex stratified by diabetes incidence"
df["Diabetes_Status"] = df["Diabetes_binary"].map({0: 'No Diabetes', 1: 'Diabetes'})

grouped = df.groupby(by="Diabetes_Status")
df0 = grouped[["PhysActivity", "BMI", "Age", "Sex"]].agg([np.mean, np.std])

df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because of the simplicity of the model and the operations required.

# ANALYSIS
## Table 1: "Multiple Linear Regression Model predicting glycemic control among individuals with diabetes, adjusting for age, sex, and BMI."
diabetes_df = df[df["Diabetes_binary"]==1]

X = diabetes_df[["PhysActivity", "BMI", "Age", "Sex"]] # independent variables
X = sm.add_constant(X) # adding a constant
Y = diabetes_df["GenHlth"] # dependent variable

model = sm.OLS(Y, X).fit()
df1 = pd.DataFrame(model.summary2().tables[1]) # Extracting the model estimates table
df1.reset_index(inplace=True)
df1['index'] = df1['index'].astype(str) # Ensure index is not purely numeric
df1.set_index('index', inplace=True)
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
 'R-squared of regression model': model.rsquared
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
