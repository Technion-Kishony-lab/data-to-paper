
# IMPORT
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, mannwhitneyu
import statsmodels.api as sm
import pickle

# LOAD DATA
df = pd.read_csv('meconium_nicu_dataset_preprocessed_short.csv')

# DATASET PREPARATIONS
# Drop rows containing missing values
df = df.dropna()

# DESCRIPTIVE STATISTICS
## Table 0: "Means and standard deviations of treatments and outcomes before and after 2015"
# Select treatments and neonatal outcome of interest, compute mean and std
desc_stat = df.groupby('PrePost')[['PPV', 'EndotrachealSuction', 'LengthStay', 'APGAR1']].agg(['mean', 'std'])
df0 = desc_stat.stack().reset_index().set_index(['PrePost', 'level_1']).transpose()
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because the variables of interest are numerical or binary.

# ANALYSIS
## Table 1: "Association between treatment policy and treatments"
# Multiple logistic regression to estimate the effect of policy while controlling for confounding variables
logit1 = sm.Logit(df['PPV'], df[['PrePost', 'AGE', 'GestationalAge', 'BirthWeight']], )
result1 = logit1.fit()
summary1 = result1.summary2()

logit2 = sm.Logit(df['EndotrachealSuction'], df[['PrePost', 'AGE', 'GestationalAge', 'BirthWeight']])
result2 = logit2.fit()
summary2 = result2.summary2()

df1 = pd.DataFrame({
    'Treatment': ['PPV', 'EndotrachealSuction'],
    'p_value': [result1.pvalues['PrePost'], result2.pvalues['PrePost']]
})
df1.set_index('Treatment', inplace=True)
df1.to_pickle('table_1.pkl')

## Table 2: "Comparison of neonatal outcomes before and after guideline implementation"
# Multiple linear regression to estimate the effect of policy on outcome while controlling for confounding variables
ols1 = sm.OLS(df['LengthStay'], df[['PrePost', 'AGE', 'GestationalAge', 'BirthWeight']])
result3 = ols1.fit()
summary3 = result3.summary2()

ols2 = sm.OLS(df['APGAR1'], df[['PrePost', 'AGE', 'GestationalAge', 'BirthWeight']])
result4 = ols2.fit()
summary4 = result4.summary2()

df2 = pd.DataFrame({
    'Outcome': ['LengthStay', 'APGAR1'],
    'p_value': [result3.pvalues['PrePost'], result4.pvalues['PrePost']]
})
df2.set_index('Outcome', inplace=True)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
