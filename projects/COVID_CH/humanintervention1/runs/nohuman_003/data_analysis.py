
# IMPORT
import pickle
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf
from sklearn.preprocessing import StandardScaler

# LOAD DATA
df_time_to_infection = pd.read_csv('TimeToInfection.csv')
df_symptoms = pd.read_csv('Symptoms.csv')

# DATASET PREPARATIONS
# Merge the two dataframes on 'ID'
df_merged = pd.merge(df_time_to_infection, df_symptoms, on='ID', how='outer')

# Remove rows with missing data
df_merged.dropna(inplace=True)

# Standardize numeric values in the merged dataframe
scaler = StandardScaler()
df_merged[['std_age_x', 'std_age_y', 'std_symptom_number']] = scaler.fit_transform(df_merged[['age_x', 'age_y', 'symptom_number']])

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of age stratified by sex and immunisation group"
df0 = df_merged.groupby(['sex_x', 'group_x'])['std_age_x'].agg(['mean', 'std'])
df0.to_pickle('table_0.pkl')


# PREPROCESSING
# Create dummy variables for categorical variables - sex, group, and variant
df_merged = pd.get_dummies(df_merged, columns=['sex_x', 'group_x', 'variant'], prefix=['sex', 'group', 'variant'], drop_first=True)

# ANALYSIS
## Table 1: "Test of association between immunity status (Group) and risk of reinfection (infection_event), accounting for sex and age."
# Logistic Regression analysis
formula = "infection_event ~ group_V + std_age_x + sex_female"
if 'sex_female' in df_merged.columns:
    logit_model = smf.logit(formula, df_merged).fit()
    df1 = pd.concat([np.exp(logit_model.params), np.exp(logit_model.conf_int()), logit_model.pvalues], axis=1)
    df1.columns = ['OR', '2.5%', '97.5%', 'p-val']
    df1.to_pickle('table_1.pkl')

## Table 2: "Test of association between booster shot (booster) and symptom count (symptom_number), accounting for immunity status."
# Independent samples t-test
group1 = df_merged[df_merged['booster'] == 1]['std_symptom_number']
group2 = df_merged[df_merged['booster'] == 0]['std_symptom_number']
t_test_results = stats.ttest_ind(group1, group2)
# confidence interval for means of both groups
CI_group1 = stats.t.interval(0.95, len(group1)-1, loc=np.mean(group1), scale=stats.sem(group1))
CI_group2 = stats.t.interval(0.95, len(group2)-1, loc=np.mean(group2), scale=stats.sem(group2))
df2 = pd.DataFrame({'mean': [np.mean(group1), np.mean(group2)],'t-statistic': [t_test_results.statistic]*2,'p-value': [t_test_results.pvalue]*2, '95% CI': [CI_group1, CI_group2]}, index=['Booster Shot=yes', 'Booster Shot=no'])
df2.to_pickle('table_2.pkl')


# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df_merged.shape[0],
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
