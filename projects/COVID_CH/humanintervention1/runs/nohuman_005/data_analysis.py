
# IMPORT
import pandas as pd
import numpy as np
import pickle
import statsmodels.formula.api as smf 

# LOAD DATA
time_to_infection = pd.read_csv('TimeToInfection.csv')
symptoms = pd.read_csv('Symptoms.csv')

# DATASET PREPARATIONS
time_to_infection_cleaned = time_to_infection.dropna(subset=['age', 'sex'])
symptoms_cleaned = symptoms.dropna(subset=['sex', 'comorbidity'])
merged = pd.merge(time_to_infection_cleaned, symptoms_cleaned, on=['ID', 'group', 'age', 'sex', 'BMI'], how='inner')

merged['BMI_numeric'] = merged['BMI'].map({'o30': 1, 'u30': 0})

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of height and age stratified by sex"
df0 = merged.groupby('sex').describe().loc[:, [('age', 'mean'), ('age', 'std'), ('BMI_numeric', 'mean'), ('BMI_numeric', 'std')]]
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
merged['sex_factorized'] = pd.factorize(merged['sex'])[0]
merged['group_factorized'] = pd.factorize(merged['group'])[0]
merged['variant_factorized'] = pd.factorize(merged['variant'])[0]

# ANALYSIS
## Table 1: "Multiple regression analysis with symptom number as dependent variable"
model = smf.ols(formula='symptom_number ~ group_factorized + BMI_numeric + age + sex_factorized', data=merged)
results = model.fit()

df1 = pd.DataFrame({
    'coef': results.params,
    'std_err': results.bse,
    'p_value': results.pvalues
})
df1.to_pickle('table_1.pkl')

## Table 2: "Descriptive statistics of symptom number grouped by group and BMI"
df2 = merged.groupby(['group_factorized', 'BMI_numeric'])['symptom_number'].agg(['mean', 'std'])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(merged),
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
