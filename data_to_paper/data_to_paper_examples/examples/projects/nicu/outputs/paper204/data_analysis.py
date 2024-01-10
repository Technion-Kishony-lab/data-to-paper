

# IMPORT
import pandas as pd
import scipy.stats as stats
import numpy as np
import pickle

# LOAD DATA
data = pd.read_csv('meconium_nicu_dataset_preprocessed_short.csv')

# DATASET PREPARATIONS
# Fill missing values for numerical variables
numerical_features = data.select_dtypes(include=[np.number]).columns.tolist()
for feature in numerical_features:
    data[feature].fillna(data[feature].mean(), inplace=True)

# Fill missing values for categorical variables. Here we use the most frequent value
categorical_features = data.select_dtypes(include=[object]).columns.tolist()
for feature in categorical_features:
    data[feature].fillna(data[feature].mode()[0], inplace=True)


# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of key variables stratified by pre-post policy implementation"
df0 = data.groupby('PrePost').agg({
    'HypertensiveDisorders':['mean', 'std'],
    'MaternalDiabetes':['mean', 'std'],
    'GestationalAge':['mean', 'std'], 
    'BirthWeight':['mean', 'std']
})
df0.index = ['Pre-Policy', 'Post-Policy']  # pretty-fying the index
df0.to_pickle('table_0.pkl')


# PREPROCESSING 
# Creating dummy variables for categorical variables
data = pd.get_dummies(data, columns=['ModeDelivery', 'Sepsis', 'Gender', 'MeconiumConsistency', 'ReasonAdmission'])


# ANALYSIS
## Table 1: "Comparison of treatment options pre and post policy implementation"
treatment_columns = ['PPV', 'EndotrachealSuction', 'CardiopulmonaryResuscitation']
df1 = pd.DataFrame()
for column in treatment_columns:
    cross_tab = pd.crosstab(data[column], data['PrePost'])
    chi2, p, dof, expected = stats.chi2_contingency(cross_tab)
    df1.loc[column, 'Chi-square'] = chi2
    df1.loc[column, 'p-value'] = p
df1.index.name = 'Treatment Options'   # setting a name for the index
df1.to_pickle('table_1.pkl')

## Table 2: "Comparison of outcomes pre and post policy implementation measured by duration of stay and Apgar scores"
outcome_columns = ['LengthStay', 'APGAR1', 'APGAR5']
df2 = pd.DataFrame()
for column in outcome_columns:
    results = stats.ttest_ind(data[data['PrePost']==0][column], 
                              data[data['PrePost']==1][column])
    df2.loc[column, 'T-statistic'] = results.statistic
    df2.loc[column, 'p-value'] = results.pvalue
df2.index.name = 'Outcome Measures'    # setting a name for the index
df2.to_pickle('table_2.pkl')


# SAVE ADDITIONAL RESULTS

additional_results = {
 'Total number of observations': len(data), 
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
