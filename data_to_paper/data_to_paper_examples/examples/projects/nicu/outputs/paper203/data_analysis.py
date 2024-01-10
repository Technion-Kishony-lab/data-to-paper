
# IMPORT
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
df = pd.read_csv('meconium_nicu_dataset_preprocessed_short.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed

# DESCRIPTIVE STATISTICS
## Table 0: "Summary of key variables before and after new policy"
numeric_columns = ['AGE', 'GestationalAge', 'BirthWeight', 'APGAR1', 'APGAR5', 'LengthStay', 'SNAPPE_II_SCORE']
mean_df = df.groupby('PrePost')[numeric_columns].mean().reset_index()
mean_df['PrePost'] = mean_df['PrePost'].map({0: 'Pre', 1: 'Post'})
mean_df.set_index('PrePost', inplace=True)
mean_df.to_pickle('table_0.pkl')

# PREPROCESSING
## Creating dummy variables for categorical variables
df = pd.get_dummies(df, columns=['ModeDelivery', 'Sepsis', 'Gender', 'MeconiumConsistency', 'ReasonAdmission'])

# ANALYSIS
## Table 1: "Association between change in new treatment policy and changes in treatments"
treatments = ['PPV', 'EndotrachealSuction', 'MeconiumRecovered', 'CardiopulmonaryResuscitation', 
              'RespiratoryReasonAdmission', 'RespiratoryDistressSyndrome', 'TransientTachypnea', 
              'MeconiumAspirationSyndrome', 'OxygenTherapy', 'MechanicalVentilation', 'Surfactant', 'Pneumothorax',
              'Breastfeeding']

df1 = pd.DataFrame()
for treatment in treatments:
    contingency_table = pd.crosstab(df['PrePost'], df[treatment])
    chi2, p, _, _ = chi2_contingency(contingency_table)
    data_row = pd.DataFrame({'Treatment': [treatment], 'Chi-square': [chi2], 'p-value': [p]})
    df1 = pd.concat([df1, data_row], ignore_index=True)

df1.set_index('Treatment', inplace=True)
df1.to_pickle('table_1.pkl')

## Table 2: "Linear regression analysis of impact of policy change on neonatal outcomes"
outcomes = ['APGAR1', 'APGAR5', 'LengthStay', 'SNAPPE_II_SCORE']

df2 = pd.DataFrame()
for outcome in outcomes:
    model = smf.ols(formula=f'{outcome} ~ PrePost', data=df)
    result = model.fit()
    data_row = pd.DataFrame({'Outcome': [outcome], 'Coeff': [result.params['PrePost']], 'p-value': [result.pvalues['PrePost']]})
    df2 = pd.concat([df2, data_row], ignore_index=True)

df2.set_index('Outcome', inplace=True)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0],
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
