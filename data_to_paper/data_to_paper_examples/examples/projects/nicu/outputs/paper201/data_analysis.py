
# IMPORT
import pandas as pd
import numpy as np
import pickle
from scipy.stats import chi2_contingency
import statsmodels.api as sm
from scipy import stats
from statsmodels.formula.api import ols

# LOAD DATA
df = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# DATASET PREPARATIONS
df = df.dropna()  # Remove rows with missing values

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics for chosen variables"
selected_cols = ['AGE', 'GRAVIDA', 'PARA', 'GestationalAge', 'BirthWeight', 'OxygenTherapy', 'LengthStay']
df0 = df[selected_cols].describe().T
df0 = df0[['mean', 'std']]  # Keeping only mean and std
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# Perform label encoding for categorical variables
categorical_vars = ['ModeDelivery', 'Sepsis', 'Gender', 'MeconiumConsistency', 'ReasonAdmission']
df[categorical_vars] = df[categorical_vars].apply(lambda x: pd.factorize(x)[0])

# ANALYSIS

# Table 1: "Comparing treatments between pre and post guideline groups using Chi-square test"
treatment_cols = ['PPV','EndotrachealSuction','MeconiumRecovered','CardiopulmonaryResuscitation','OxygenTherapy']
df1 = pd.DataFrame(columns=["Treatment", "Chi2 Value", "p-value"])
for col in treatment_cols:
    chi2, p, dof, ex = chi2_contingency(pd.crosstab(df['PrePost'], df[col]))
    df1 = pd.concat([df1, pd.DataFrame({"Treatment": [col], "Chi2 Value": [chi2], "p-value": [p]})])

df1.to_pickle('table_1.pkl')

# Table 2: "Comparing neonatal outcomes between pre and post guideline groups using T-test controlling for confounders of AGE and ModeDelivery"
outcome_cols = ['GestationalAge', 'BirthWeight', 'APGAR1', 'APGAR5', 'LengthStay']
df2 = pd.DataFrame(columns=["Outcome Measures", "p-value", "F Value"])
for col in outcome_cols:
    model = ols(f'{col} ~ C(PrePost) + AGE + C(ModeDelivery)', data=df).fit()
    anova_result = sm.stats.anova_lm(model, typ=2)
    df2 = pd.concat([df2, pd.DataFrame({"Outcome Measures": [col], "p-value": [anova_result.loc['C(PrePost)','PR(>F)']], "F Value": [anova_result.loc['C(PrePost)','F']]})])

df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0]
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
