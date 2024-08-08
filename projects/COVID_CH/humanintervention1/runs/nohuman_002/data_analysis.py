
# IMPORT
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pickle
import scipy.stats as stats

# LOAD DATA
time_to_infection = pd.read_csv('TimeToInfection.csv')
symptoms = pd.read_csv('Symptoms.csv')

# DATASET PREPARATIONS
# Merge datasets on ID and adequate fields
merged_data = pd.merge(time_to_infection, symptoms, on = ["ID", "group", "age", "sex", "BMI"], how = 'inner')

# PREPROCESSING
# Create dummy variables for 'group', 'sex', and 'BMI'
merged_data = pd.get_dummies(merged_data, columns = ['sex', 'BMI'], prefix = ['sex', 'BMI'], drop_first = True)

# DESCRIPTIVE STATISTICS
## Table 0: Descriptive statistics of the merged dataset
df0 = merged_data[['symptom_number', 'age']].agg(['mean', 'std', 'count'])
df0.loc['ci', :] = df0.loc['std', :] / np.sqrt(df0.loc['count', :]) * 1.96  # 95% CI
df0.to_pickle('table_0.pkl')

# ANALYSIS
## Table 1: Test of association between vaccination status and symptom numbers for vaccinated-only, infected-only and hybrid groups
merged_data_grouped = merged_data.groupby('group')
group_V = merged_data_grouped.get_group('V')['symptom_number']
group_I = merged_data_grouped.get_group('I')['symptom_number']
group_H = merged_data_grouped.get_group('H')['symptom_number']
test_V_I = stats.ttest_ind(group_V, group_I)
test_V_H = stats.ttest_ind(group_V, group_H)
test_H_I = stats.ttest_ind(group_H, group_I)

df1 = pd.DataFrame({
    'group_V': [group_V.mean(), group_V.std(), len(group_V), group_V.std() / np.sqrt(len(group_V)) * 1.96],
    'group_I': [group_I.mean(), group_I.std(), len(group_I), group_I.std() / np.sqrt(len(group_I)) * 1.96],
    'group_H': [group_H.mean(), group_H.std(), len(group_H), group_H.std() / np.sqrt(len(group_H)) * 1.96],
}, index=['mean', 'std', 'count', 'ci'])

df1_tests = pd.DataFrame({
    'V vs I': [test_V_I.statistic, test_V_I.pvalue], 
    'V vs H': [test_V_H.statistic, test_V_H.pvalue], 
    'H vs I': [test_H_I.statistic, test_H_I.pvalue]
}, index=['t-statistic', 'p-value'])

df1 = pd.concat([df1, df1_tests]).fillna('-')
df1.to_pickle('table_1.pkl')

## Table 2: ANCOVA of symptom number on age and comorbidity
model = smf.ols('symptom_number ~ age + comorbidity', data=merged_data).fit()
summary_table = model.summary2().tables[1]
df2 = pd.DataFrame(summary_table.values, columns=summary_table.columns, index=summary_table.index)[['Coef.', 'Std.Err.', 'P>|t|']]
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'total observations': len(merged_data),
    'mean age': merged_data['age'].mean(),
    'std age': merged_data['age'].std(),
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
