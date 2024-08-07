
# IMPORT
import pandas as pd
import numpy as np
import pickle
from statsmodels.formula.api import ols
from sklearn.preprocessing import StandardScaler

# LOAD DATA
data_infection = pd.read_csv('TimeToInfection.csv')
data_symptoms = pd.read_csv('Symptoms.csv')

# DATASET PREPARATIONS
# Merge the two dataframes based on 'ID' and 'group'
data_all = pd.merge(data_infection, data_symptoms, on=['ID', 'group'])
data_infected = data_all[data_all['infection_event'] == 1].drop_duplicates(subset='ID')

# Convert 'positive_household' to binary
data_infected['positive_household_binary'] = data_infected['positive_household'].map({'yes': 1, 'no': 0})

# Exclude unimmunised group
data_infected_immunised = data_infected[data_infected['group'] != 'N']

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of infection events, mean symptoms & mean time since last infection per group"
summary_infection_events = data_all.groupby('group')['infection_event'].sum()
summary_avg_symptoms = data_infected.groupby('group')['symptom_number'].mean()
summary_avg_time_since_immunisation = data_infected.groupby('group')['months_since_immunisation'].mean()

df0 = pd.DataFrame({'InfectionEvents': summary_infection_events, 
                    'MeanSymptoms': summary_avg_symptoms,
                    'MeanMonthsSinceImmunisation': summary_avg_time_since_immunisation})

# Replacing NaN values with "NA" for group N
df0.fillna("NA", inplace=True)
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# Data Standardization
scaler = StandardScaler()
scaled_data = scaler.fit_transform(data_infected_immunised[['age_x', 'months_since_immunisation']])
scaled_df = pd.DataFrame(scaled_data, index=data_infected_immunised.index, columns=['scaled_age', 'scaled_months_since_immunisation'])
data_infected_immunised = pd.concat([data_infected_immunised, scaled_df], axis=1)

# Creating dummy variables for categorical variables
data_infected_immunised = pd.get_dummies(data_infected_immunised, drop_first=True)

# Creating interaction terms
data_infected_immunised['group_V_interaction'] = data_infected_immunised['group_V'] * data_infected_immunised['scaled_months_since_immunisation']
data_infected_immunised['group_I_interaction'] = data_infected_immunised['group_I'] * data_infected_immunised['scaled_months_since_immunisation']

# ANALYSIS
## Table 1: "Association between months_since_immunisation and symptom_number, including interaction between group and time since immunisation"
model1 = ols('symptom_number ~ scaled_months_since_immunisation + group_V + group_I + group_V_interaction + group_I_interaction', 
             data=data_infected_immunised).fit()
table1 = model1.summary2().tables[1]
table1.to_pickle('table_1.pkl')

## Table 2: "Association between patient_contact & symptom_number, adjusted for mask usage & household infections"
model2 = ols('symptom_number ~ patient_contact + using_FFP2_mask_x + positive_household_binary', 
             data=data_infected_immunised).fit()
table2 = model2.summary2().tables[1]
table2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data_all),
    'Number of immunised and infected health workers': len(data_infected_immunised),
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
