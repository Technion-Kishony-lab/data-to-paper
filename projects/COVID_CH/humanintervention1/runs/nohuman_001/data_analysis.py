
# IMPORT
import pandas as pd
import numpy as np
from statsmodels.formula.api import glm
import statsmodels.api as sm
import pickle

# LOAD DATA
time_to_infection_data = pd.read_csv('TimeToInfection.csv')
symptoms_data = pd.read_csv('Symptoms.csv')

# DATASET PREPARATIONS
time_to_infection_data.fillna(np.nan, inplace=True)
symptoms_data.fillna(np.nan, inplace=True)

merged_data = pd.merge(time_to_infection_data, symptoms_data, how = 'inner', on = ['ID','group','age','sex','BMI'],suffixes= ('', '_symptoms'))

# DESCRIPTIVE STATISTICS
# No descriptive statistics are needed.

# PREPROCESSING
merged_data = pd.concat([merged_data,pd.get_dummies(merged_data['group'], prefix='group')], axis=1)
merged_data = pd.concat([merged_data,pd.get_dummies(merged_data['sex'], prefix='sex')], axis=1)
merged_data = pd.concat([merged_data,pd.get_dummies(merged_data['BMI'], prefix='BMI')], axis=1)
merged_data = merged_data.drop(['group', 'sex', 'BMI', 'vaccinetype', 'group_H'], axis = 1)

# ANALYSIS
## Table 1: "Association between vaccination status and time until reinfection"
formula1 = 'months_until_reinfection ~ age + group_N + group_V + group_I + sex_female + BMI_u30 + patient_contact + using_FFP2_mask'
model1 = glm(formula1, data=merged_data, family=sm.families.Gaussian()).fit()
df1 = pd.DataFrame(model1.summary2().tables[1])
df1.to_pickle('table_1.pkl')

## Table 2: "Association between vaccination status and number of symptoms at reinfection"
formula2 = 'symptom_number ~ age + group_N + group_V + group_I + sex_female + BMI_u30 + patient_contact + using_FFP2_mask'
model2 = glm(formula2, data=merged_data, family=sm.families.Gaussian()).fit()
df2 = pd.DataFrame(model2.summary2().tables[1])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(merged_data),         
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

