

# IMPORT
import pandas as pd
import numpy as np
import pickle
from statsmodels.discrete.discrete_model import Logit
from statsmodels.regression.linear_model import OLS

# LOAD DATA
df_time_to_infection = pd.read_csv('TimeToInfection.csv')

# DATASET PREPARATIONS
# Calculate the duration for each interval
df_time_to_infection['interval_length'] = df_time_to_infection['day_interval_stop'] - df_time_to_infection['day_interval_start']

# Aggregate data by ID to get total time at risk and whether an infection occured
df_time_to_infection = df_time_to_infection.groupby('ID').agg({'interval_length':'sum', 'group':'first',
  'age':'first', 'sex':'first', 'BMI': 'first',
  'infection_event':'max'}).reset_index()
df_time_to_infection.rename(columns={'interval_length': 'total_time_at_risk'}, inplace=True)

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# Handle missing data
df_time_to_infection.loc[df_time_to_infection['sex'] == '', 'sex'] = np.NaN
df_time_to_infection.loc[df_time_to_infection['age'].isna(), 'age'] = df_time_to_infection['age'].mean()

# Create dummy variables for the 'group' column 
df = pd.get_dummies(df_time_to_infection, columns=['group'], drop_first=False)

# ANALYSIS
## Table 1: "Impact of vaccination group on infection event and total time at risk"
model = Logit.from_formula('infection_event ~ total_time_at_risk + group_V + group_I + group_H', df)
result = model.fit()
df1 = pd.DataFrame(result.summary2().tables[1])
df1.to_pickle('table_1.pkl')

## Table 2: "Vaccination group impact on total time at risk among infected individuals"
df_infected = df[df['infection_event'] == 1]
# As the sum of group_V, group_I, group_H, and group_N equals 1, we can remove group_N to avoid singularity
model2 = OLS.from_formula('total_time_at_risk ~ group_V + group_I + group_H', df_infected)
result2 = model2.fit()
df2 = pd.DataFrame(result2.summary2().tables[1])
df2.to_pickle('table_2.pkl')

## Table 3: "Distribution of infection events by vaccination group"
grouped_df = df_time_to_infection.groupby('group').agg({'total_time_at_risk':'mean', 'infection_event':'sum'})
grouped_df['infection_rate'] = grouped_df['infection_event'] / grouped_df['total_time_at_risk']
df3 = grouped_df[['infection_rate']]
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0],
    'Log-Likelihood of model': result.llf,
    'AIC of model with Total Time at Risk Among Infected Individuals': result2.aic
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
