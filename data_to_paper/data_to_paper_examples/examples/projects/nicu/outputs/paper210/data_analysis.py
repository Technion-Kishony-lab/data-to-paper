
# IMPORT
import pandas as pd
import pickle
from scipy.stats import chi2_contingency
import statsmodels.formula.api as smf

# LOAD DATA
df = pd.read_csv('meconium_nicu_dataset_preprocessed_short.csv')

# DATASET PREPARATIONS
# Remove rows with missing values
df = df.dropna()

# Standardize gestational age to weeks (it is originally in days)
df["GestationalAge"] = df["GestationalAge"]/7 

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of neonate interventions and outcomes stratified by new policy"
df0 = df.groupby('PrePost').agg({'PPV': ['mean', 'std'], 'EndotrachealSuction': ['mean', 'std'], 'LengthStay': ['mean', 'std'], 'APGAR1': ['mean', 'std'], 'APGAR5': ['mean', 'std']})
df0.index = ["Pre Policy", "Post Policy"]
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# Creating dummy variables for categorical variables
df = pd.get_dummies(df,columns=['ModeDelivery','Sepsis','Gender','MeconiumConsistency','ReasonAdmission'])

# ANALYSIS
# Table 1: "Test of association between new policy implementation and interventions"
contingency1 = pd.crosstab(df['PrePost'], df['PPV'])
contingency2 = pd.crosstab(df['PrePost'], df['EndotrachealSuction'])
_, pval1, _, _ = chi2_contingency(contingency1)
_, pval2, _, _ = chi2_contingency(contingency2)
df1 = pd.DataFrame({"Intervention": ["PPV", "EndotrachealSuction"], "p-value": [pval1, pval2]})
df1.set_index("Intervention", inplace=True)
df1.to_pickle('table_1.pkl')

# Table 2: "Test of association between new policy and neonatal outcomes"
model1 = smf.ols(formula="LengthStay ~ PrePost + AGE + GRAVIDA + HypertensiveDisorders + MaternalDiabetes", data=df).fit()
model2 = smf.ols(formula="APGAR1 ~ PrePost + AGE + GRAVIDA + HypertensiveDisorders + MaternalDiabetes", data=df).fit()
model3 = smf.ols(formula="APGAR5 ~ PrePost + AGE + GRAVIDA + HypertensiveDisorders + MaternalDiabetes", data=df).fit()
df2 = pd.DataFrame({"Outcome": ["LengthStay", "APGAR1", "APGAR5"], "p-value": [model1.pvalues['PrePost'], model2.pvalues['PrePost'], model3.pvalues['PrePost']]})
df2.set_index("Outcome", inplace=True)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
 'accuracy of regression model for LengthStay': model1.rsquared,
 'accuracy of regression model for APGAR1': model2.rsquared,
 'accuracy of regression model for APGAR5': model3.rsquared,
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
 