
# IMPORT
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of weight stratified by sex"
df0 = df.groupby('sex')['wt'].agg(['mean', 'std']).reset_index()

# Create a new series for Gender
df0['Gender'] = df0['sex'].replace({0: 'Female', 1: 'Male'})
df0.set_index('Gender', inplace=True)

# Save dataframe
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# Create dummy variable for sex
df = pd.get_dummies(df, columns=['sex'], drop_first=True)

# ANALYSIS
## Table 1: "Linear regression model with interaction between weight and sex predicting OTTD"
model = smf.ols(formula="tube_depth_G ~ wt * sex_1", data=df)
results = model.fit()

df1 = pd.DataFrame(np.array([results.params, results.conf_int().iloc[:, 0], 
                             results.conf_int().iloc[:, 1], results.pvalues, results.bse]).T,
                   columns=['coef','ci_low','ci_high','pval', 'std err'])

df1['Parameter'] = ['Intercept', 'Weight', 'Sex', 'Weight:Sex']
df1.set_index('Parameter', inplace=True)

# Save dataframe
df1.to_pickle('table_1.pkl')

## Table 2: "Polynomial regression model with weight predicting OTTD"
# Create a new column for the square of weight
df['wt_sq'] = df['wt']**2

model2 = smf.ols(formula="tube_depth_G ~ wt + wt_sq", data=df)
results2 = model2.fit()

df2 = pd.DataFrame(np.array([results2.params, results2.conf_int().iloc[:, 0], 
                              results2.conf_int().iloc[:, 1], results2.pvalues, results2.bse]).T,
                    columns=['coef','ci_low','ci_high','pval', 'std err'])

df2['Parameter'] = ['Intercept', 'Weight', 'Weight (squared)']
df2.set_index('Parameter', inplace=True)

# Save dataframe
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0],
    'R-squared of linear model': results.rsquared,
    'R-squared of polynomial model': results2.rsquared
}

# Save additional results
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
