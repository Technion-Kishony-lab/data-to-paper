
# IMPORT
import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
import pickle

# LOAD DATA
df = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# DATASET PREPARATIONS
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

# DESCRIPTIVE STATISTICS
df0 = df.groupby('PrePost').agg(
    PPV=('PPV', 'mean'), EndotrachealSuction=('EndotrachealSuction', 'mean'), 
    AntibioticsDuration=('AntibioticsDuration', 'mean'), LengthStay=('LengthStay', 'mean'))
df0.index = ['Pre', 'Post']
df0.to_pickle('table_0.pkl')

# PREPROCESSING
df = pd.get_dummies(df, columns=['ModeDelivery', 'Sepsis', 'Gender', 'MeconiumConsistency', 'ReasonAdmission'])

# ANALYSIS
X = df.select_dtypes(include=[np.number])  # select numeric columns
X = X.drop(['PPV', 'EndotrachealSuction', 'AntibioticsDuration', 'LengthStay'], axis=1)
X = sm.add_constant(X)

# Table 1: Test of association between policy change and PPV
Y = df['PPV']
model = sm.OLS(Y,X)
results = model.fit()
df1 = pd.DataFrame({'coef': results.params, 'p-value': results.pvalues})
df1 = df1[df1['p-value']<0.05]
df1.to_pickle('table_1.pkl')

# Table 2: Test of association between policy change and LengthStay
Y = df['LengthStay']
model = sm.OLS(Y,X)
results = model.fit()
df2 = pd.DataFrame({'coef': results.params, 'p-value': results.pvalues})
df2 = df2[df2['p-value']<0.05]
df2.to_pickle('table_2.pkl')

# Table 3: Test of association between policy change and Antibiotics Duration
Y = df['AntibioticsDuration']
model = sm.OLS(Y,X)
results = model.fit()
df3 = pd.DataFrame({'coef': results.params, 'p-value': results.pvalues})
df3 = df3[df3['p-value']<0.05]
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
 'accuracy of regression model': results.rsquared,
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
