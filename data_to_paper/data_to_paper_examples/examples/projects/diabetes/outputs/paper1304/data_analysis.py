

# IMPORT
import pandas as pd
import pickle
import statsmodels.api as sm

# LOAD DATA
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# DATASET PREPARATIONS
# Any value over 90 in any of the columns considered to be undefined/missing. 
# We will exclude these rows from our analysis.
df_cleaned = df[df.lt(90).all(axis=1)]

# DESCRIPTIVE STATISTICS
## Table 0: "Mean values of physical activity, BMI, age, and potential confounders stratified by diabetes status"
df0 = df_cleaned.groupby('Diabetes_binary')[['PhysActivity', 'BMI', 'Age', 'Sex', 'Education', 'Income']].mean()
df0.index = ['No Diabetes', 'Diabetes']
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed, because all the variables we are interested in are already in the appropriate format.

# ANALYSIS
## Table 1: "Logistic regression of diabetes status on physical activity, BMI, age, and their interaction terms, adjusting for sex, education, and income"
y = df_cleaned['Diabetes_binary']
X = df_cleaned[['PhysActivity', 'BMI', 'Age', 'Sex', 'Education', 'Income']]
X['PhysActivity_BMI'] = df_cleaned['PhysActivity'] * df_cleaned['BMI']
X['PhysActivity_Age'] = df_cleaned['PhysActivity'] * df_cleaned['Age']
X = sm.add_constant(X)
logit_model = sm.Logit(y, X)
result = logit_model.fit()

df1 = pd.DataFrame({
    'coef': result.params.values,
    'std err': result.bse, 
    'pvalue': result.pvalues,
    '[0.025': result.conf_int()[0],
    '0.975]': result.conf_int()[1]}, 
    index=result.params.index)

df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df_cleaned),
 'Pseudo R-squ of regression model': result.prsquared
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
