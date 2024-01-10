
# IMPORT
import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
data = pd.read_csv('meconium_nicu_dataset_preprocessed_short.csv')

# DATASET PREPARATIONS
numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()    # This is now a list of columns
data[numeric_columns] = data[numeric_columns].fillna(data[numeric_columns].median())

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of key variables stratified by PrePost"
description_variables = ['AGE', 'BirthWeight', 'AntibioticsDuration', 'LengthStay', 'APGAR1', 'APGAR5']
df0 = data.groupby('PrePost')[description_variables].mean()
index_names = ['PrePolicy', 'PostPolicy']
df0.index = index_names
df0.to_pickle('table_0.pkl')

# PREPROCESSING
data = pd.get_dummies(data, columns=['ModeDelivery', 'Sepsis', 'Gender', 'MeconiumConsistency', 'ReasonAdmission'], drop_first=True)

# ANALYSIS
## Table 1: "Changes in treatment following policy change"
treatment_vars = ['EndotrachealSuction', 'PPV', 'OxygenTherapy', 'MechanicalVentilation', 'Surfactant']
chi2_p_values = [stats.chi2_contingency(pd.crosstab(data['PrePost'], data[var]))[1] for var in treatment_vars]
df1 = pd.DataFrame({'Treatment': treatment_vars, 'Chi2_p_value': chi2_p_values}, index=np.arange(1, len(treatment_vars) + 1, 1).astype(str))
df1.to_pickle('table_1.pkl')

## Table 2: "Changes in neonatal outcomes following policy change"
outcome_vars = ['APGAR1', 'APGAR5', 'LengthStay', 'Breastfeeding', 'SNAPPE_II_SCORE']
t_stat, p_values = [], []
for var in outcome_vars:
    t_res = stats.ttest_ind(data[data['PrePost'] == 0][var], data[data['PrePost'] == 1][var])
    t_stat.append(t_res.statistic)
    p_values.append(t_res.pvalue)
df2 = pd.DataFrame({'Outcome': outcome_vars, 't_stat': t_stat, 'p_value': p_values}, index=np.arange(1, len(outcome_vars) + 1, 1).astype(str))
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data) 
    # other relevant metrics can be added here
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
