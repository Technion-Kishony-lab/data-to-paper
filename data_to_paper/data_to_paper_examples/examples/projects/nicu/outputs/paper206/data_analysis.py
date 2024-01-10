
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import LabelEncoder
import pickle

# LOAD DATA
df = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# DATASET PREPARATIONS
df['ProlongedRupture'].fillna(df['ProlongedRupture'].mean(), inplace=True)
df['Chorioamnionitis'].fillna(df['Chorioamnionitis'].mode()[0], inplace=True)
df['SNAPPE_II_SCORE'].fillna(df['SNAPPE_II_SCORE'].median(), inplace=True)

# DESCRIPTIVE STATISTICS
## Table 0: "Selected descriptive statistics of the dataset stratified by policy change"
means = df.groupby('PrePost')[['AGE', 'BirthWeight', 'GestationalAge', 'LengthStay', 'SNAPPE_II_SCORE']].mean()
counts = df.groupby('PrePost')[['ModeDelivery', 'Sepsis', 'Gender', 'MeconiumConsistency', 'ReasonAdmission']].apply(lambda x: x.mode().iloc[0])
df0 = pd.concat([means, counts], axis=1)
df0.index = ['Before Policy Change', 'After Policy Change']
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
le = LabelEncoder()
df['ModeDelivery'] = le.fit_transform(df['ModeDelivery'])
df['Sepsis'] = le.fit_transform(df['Sepsis'])
df['Gender'] = le.fit_transform(df['Gender'])
df['MeconiumConsistency'] = le.fit_transform(df['MeconiumConsistency'])
df['ReasonAdmission'] = le.fit_transform(df['ReasonAdmission'])

# ANALYSIS
## Table 1: "Test of treatment changes due to policy changes"
contingency_table = pd.crosstab(index=df['PrePost'], columns=[df['PPV'], df['EndotrachealSuction']])
chi2, p_val, dof, _ = stats.chi2_contingency(contingency_table)
df1 = pd.DataFrame({'Chi-square Statistic': chi2, 'p-value': p_val}, index=[0])
df1.index = ['Treatments Changes']
df1.to_pickle('table_1.pkl')

## Table 2: "Test of neonatal outcomes due to policy changes"
rank_sum, p_val = stats.mannwhitneyu(df[df['PrePost'] == 0]['LengthStay'], df[df['PrePost'] == 1]['LengthStay'])
df2 = pd.DataFrame({'Mann-Whitney U Statistic': rank_sum, 'p-value': p_val}, index=[0])
df2.index = ['Neonatal Outcomes']
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {'Total number of observations': len(df.index)}
with open('additional_results.pkl', 'wb') as f:
     pickle.dump(additional_results, f)
