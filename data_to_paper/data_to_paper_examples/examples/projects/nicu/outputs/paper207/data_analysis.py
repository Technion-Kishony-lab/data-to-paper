
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.formula.api import ols
import pickle
import scipy.stats as stats

# LOAD DATA
df = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# DATASET PREPARATIONS
# Checking for any missing values and fill them with appropriate method if there are any.
# Fill numerical columns with mean and fill the categorical columns with mode (most frequent value)
for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]):
        df[col] = df[col].fillna(df[col].mean())
    else:
        df[col] = df[col].fillna(df[col].mode()[0])

# DESCRIPTIVE STATISTICS 
# No descriptive statistics table is needed.

# PREPROCESSING
# Creating dummy variables for categorical variables
df = pd.get_dummies(df, columns=['ModeDelivery', 'Gender', 'MeconiumConsistency'], drop_first=True)

# ANALYSIS

## Table 1: "Test of association between treatment policy change and neonatal treatments"
# Chi-square test for independence for PPV and EndotrachealSuction.
chi_result_ppv = stats.chi2_contingency(pd.crosstab(df.PrePost, df.PPV))
chi_result_suction = stats.chi2_contingency(pd.crosstab(df.PrePost, df.EndotrachealSuction))
df1 = pd.DataFrame({
    'treatment': ['PPV', 'EndotrachealSuction'],
    'chi-square': [chi_result_ppv[0], chi_result_suction[0]],
    'p-value': [chi_result_ppv[1], chi_result_suction[1]]
})
df1.set_index('treatment', inplace=True)
df1.to_pickle('table_1.pkl')

## Table 2: "Test of association between the change in treatment policy and neonatal outcomes"
# Two-sample T-test for LengthStay, APGAR1, APGAR5.
res_lenstay = stats.mannwhitneyu(df[df.PrePost == 0].LengthStay, df[df.PrePost == 1].LengthStay)
res_apgar1 = stats.mannwhitneyu(df[df.PrePost == 0].APGAR1, df[df.PrePost == 1].APGAR1)
res_apgar5 = stats.mannwhitneyu(df[df.PrePost == 0].APGAR5, df[df.PrePost == 1].APGAR5)

df2 = pd.DataFrame({
    'outcome_variable': ['LengthStay', 'APGAR1', 'APGAR5'],
    'U_statistic': [res_lenstay.statistic, res_apgar1.statistic, res_apgar5.statistic],
    'p-value': [res_lenstay.pvalue, res_apgar1.pvalue, res_apgar5.pvalue]
})
df2.set_index('outcome_variable', inplace=True)
df2.to_pickle('table_2.pkl')

## Table 3: Comparison of the distribution of confounding variables between the pre-guideline and post-guideline groups.
confounding_vars = ['AGE', 'GestationalAge', 'ModeDelivery_VAGINAL']
df3 = df.groupby('PrePost')[confounding_vars].mean()
df3.index = ['PrePolicy', 'PostPolicy']  # Changing the index to have meaningful labels
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {'Total number of observations': df.shape[0]}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
