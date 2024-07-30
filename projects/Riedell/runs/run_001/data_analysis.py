
# IMPORT
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import pickle
from scipy.stats import chi2_contingency

# LOAD DATA
df = pd.read_csv('data.csv')

# DATASET PREPARATIONS
## Replace 99 and 98 with NaN for handling missing data
df.replace([99, 98], np.nan, inplace=True)
## Create binary variables for sex (1 if Male else 0)
df['Male'] = (df['sex'] == 1).astype(int)

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of age group and sex stratified by survival and event"
groups = df.groupby(['dead', 'sex'])['agegp']
df0 = pd.concat([groups.mean().rename('mean'), groups.std().rename('std')], axis=1)
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed, because the dataset is already in a suitable format for analysis.

# ANALYSIS
## Table 1: "Impact of age and sex on overall survival, factoring in Karnofsky score and stage of organ involvement"
model1 = smf.logit("dead ~ agegp + Male + kps + stagedxn", data=df)
result1 = model1.fit()
## Creating a new dataframe for Table 1
df1 = pd.DataFrame({'Coefficients': result1.params, 'p-value': result1.pvalues, 
                    'Odds Ratio': np.exp(result1.params), 
                    'Odds Ratio 2.5%': np.exp(result1.conf_int()[0]),
                    'Odds Ratio 97.5%':  np.exp(result1.conf_int()[1])})
df1['p-value summary'] = df1['p-value'].apply(lambda x: '***' if x <= 0.01 else '**' if x <= 0.05 else '*' if x <=0.1 else '' )
df1.to_pickle('table_1.pkl')

## Table 2: "Association between year of transplant and overall survival, factoring in age and gender"
table = pd.crosstab(df['yeartxgp'], df['dead'])
chi2_test_result = chi2_contingency(table)
df2 = pd.DataFrame({"Chi-Square Test Statistic": [chi2_test_result.statistic], "p-value": [chi2_test_result.pvalue]}, index=['Year of Transplant'])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
