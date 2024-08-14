

# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
TimeToInfection = pd.read_csv("TimeToInfection.csv")
Symptoms = pd.read_csv("Symptoms.csv")

# DATASET PREPARATIONS
# Drop the rows that contain missing value in the 'sex' column
TimeToInfection.dropna(subset=['sex'], inplace=True)
Symptoms.dropna(subset=['sex'], inplace=True)

# Join Data files
df = pd.merge(TimeToInfection[TimeToInfection.infection_event == 1], Symptoms, on=['ID', 'group', 'age', 'sex', 'BMI'], suffixes=('_x', '_y'))

# DESCRIPTIVE STATISTICS
## Table 0: "Distribution of group, symptom number and variant for infected individuals only"
grouped_df = df.groupby(['group', 'variant']).agg({'symptom_number': ['mean', 'std', 'count']}).reset_index()
df0 = pd.DataFrame(grouped_df)
df0.columns = ['Group', 'Variant', 'Average Symptom Number', 'Standard Deviation', 'Count']
df0.set_index(['Group', 'Variant'], inplace=True)
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed in this case

# ANALYSIS
## Table 1: "Association between symptom numbers and group, variant, adjusting for age, sex, and comorbidity for infected individuals only"
formula1 = 'symptom_number ~ group + variant + age + sex + comorbidity'
model1 = smf.ols(formula1, data=df)
results1 = model1.fit()
table1 = pd.DataFrame({'coef': results1.params, 'p-value': results1.pvalues})
table1.to_pickle('table_1.pkl')

## Table 2: "Association between symptom numbers and variant, adjusting for age, sex, comorbidity and interaction between group and variant for infected individuals only"
formula2 = 'symptom_number ~ group + variant + group:variant + age + sex + comorbidity' # Create interaction term
model2 = smf.ols(formula2, data=df)
results2 = model2.fit()
# Include interaction term in the result table
table2 = pd.DataFrame({'coef': results2.params, 'p-value': results2.pvalues})
table2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0],
    'Number of comorbidity cases': df['comorbidity'].sum(),
    'Number of people using FFP2 mask': df['using_FFP2_mask_y'].sum()
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

