
# IMPORT
import pickle
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, sem
from sklearn.preprocessing import LabelEncoder
from statsmodels.formula.api import ols

# LOAD DATA
timing_df = pd.read_csv('TimeToInfection.csv')
symptoms_df = pd.read_csv('Symptoms.csv')

# DATASET PREPARATIONS
merged_df = pd.merge(timing_df, symptoms_df, on='ID', suffixes=['_timing', '_symptoms'])

# Fill missing values and add as new features
merged_df['patient_contact_filled'] = merged_df['patient_contact'].fillna(0)
merged_df['using_FFP2_mask_timing_filled'] = merged_df['using_FFP2_mask_timing'].fillna(0)
merged_df['sex_timing_filled'] = merged_df['sex_timing'].fillna('Unknown')
merged_df['comorbidity_filled'] = merged_df['comorbidity'].fillna(0)

# Define severe symptoms 
merged_df['severe_symptoms'] = np.where(merged_df['symptom_number'] > 5, 1, 0)

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of age and number of symptoms stratified by group"
gp = merged_df.groupby('group_timing')
df0 = gp.agg({'age_timing': ['min', 'max', 'mean', sem], 
              'symptom_number': ['min', 'max', 'mean', sem]}).reset_index()
df0.columns  = [' '.join(col).strip() for col in df0.columns.values]
df0.set_index('group_timing', inplace=True)

# save table0
df0.to_pickle('table_0.pkl')

# PREPROCESSING
le = LabelEncoder()
merged_df['sex_timing_encoded'] = le.fit_transform(merged_df['sex_timing_filled'])
merged_df['group_timing_encoded'] = le.fit_transform(merged_df['group_timing'])
merged_df['BMI_timing_encoded'] = le.fit_transform(merged_df['BMI_timing'])
merged_df['variant_encoded'] = le.fit_transform(merged_df['variant'])

# ANALYSIS
## Table 1: "Test of association between group timing and severe symptoms"
olr1 = ols(formula='severe_symptoms ~ C(group_timing_encoded)', data=merged_df).fit()
df1 = pd.DataFrame(olr1.summary2().tables[1])
df1.to_pickle('table_1.pkl')

## Table 2: "Test of association between comorbidity_filled and severe symptoms"
olr2 = ols(formula='severe_symptoms ~ comorbidity_filled', data=merged_df).fit()
df2 = pd.DataFrame(olr2.summary2().tables[1])
df2.to_pickle('table_2.pkl')

## Table 3: "Test of interaction between group timing and comorbidity_filled"
olr3 = ols(formula='severe_symptoms ~ C(group_timing_encoded) * comorbidity_filled', data=merged_df).fit()
df3 = pd.DataFrame(olr3.summary2().tables[1])
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(merged_df),
    'Adjusted R squared Table 1': olr1.rsquared_adj,
    'Adjusted R squared Table 2': olr2.rsquared_adj,
    'Adjusted R squared Table 3': olr3.rsquared_adj, 
    'Confidence Interval': olr3.conf_int().values,
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
