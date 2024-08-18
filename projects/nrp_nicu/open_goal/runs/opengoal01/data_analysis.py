
# IMPORT
import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
data = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of important numerical variables across the Pre and Post policy implementation groups"
groupby_data = data.groupby('PrePost')[['AGE', 'GestationalAge', 'BirthWeight']].agg(['mean', 'std'])
df0 = groupby_data.unstack().reset_index().rename(columns={'level_0': 'Variable', 'level_1': 'Statistic', 0: 'Value'})
df0['Row_Labels'] = df0['Variable'] + ' (' + df0['Statistic'] + ')'
df0.set_index('Row_Labels', inplace=True)
df0.drop(columns=['Variable', 'Statistic'], inplace=True)
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# Creating dummy variables for categorical variables
data_prep = pd.get_dummies(data)

# ANALYSIS
## Table 1: "Test of association between policy change and rates of EndotrachealSuction and MechanicalVentilation, considering confounding factors"
# Chi-squared test with Yates' correction
chi_res1 = stats.chi2_contingency(pd.crosstab([data['PrePost'], data['AGE']], data['EndotrachealSuction']), correction=True)
chi_res2 = stats.chi2_contingency(pd.crosstab([data['PrePost'], data['AGE']], data['MechanicalVentilation']), correction=True)

df1 = pd.DataFrame({
    'Variable': ['EndotrachealSuction', 'MechanicalVentilation'],
    'chi-square': [chi_res1.statistic, chi_res2.statistic],
    'p-value': [chi_res1.pvalue, chi_res2.pvalue],
    'df': [chi_res1.dof, chi_res2.dof]
})

df1.set_index('Variable', inplace=True)
df1.to_pickle('table_1.pkl')

## Table 2: "Logistic regression impact of the NRP guideline change on occurrence of MeconiumAspirationSyndrome, RespiratoryDistressSyndrome, and Pneumothorax; considers confounders"
health_outcomes = ['MeconiumAspirationSyndrome', 'RespiratoryDistressSyndrome', 'Pneumothorax']
model_data = data.dropna(subset=health_outcomes+['AGE', 'GestationalAge', 'Gender'])

df2 = pd.DataFrame(columns=health_outcomes, index=['OR', 'p-value', 'Significant'])

for outcome in health_outcomes:
    model = smf.logit(f"{outcome} ~ PrePost + AGE + GestationalAge + C(Gender)", data=model_data)
    result = model.fit()
    odds_ratio = np.exp(result.params)['PrePost']
    pvalue = result.pvalues['PrePost']
    df2.loc['OR', outcome] = odds_ratio
    df2.loc['p-value', outcome] = pvalue
    df2.loc['Significant', outcome] = 'Yes' if pvalue < 0.05 else 'No' # Add significance indicator

df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data)
}

with open('additional_results.pkl', 'wb') as f:
     pickle.dump(additional_results, f)
