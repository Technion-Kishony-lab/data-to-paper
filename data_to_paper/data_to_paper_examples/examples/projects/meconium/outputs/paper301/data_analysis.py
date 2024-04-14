
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
from sklearn import preprocessing
from sklearn.utils import resample
import pickle

# LOAD DATA
data = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# DATASET PREPARATIONS
numeric_data = data.select_dtypes(include=[np.number])
categorical_data = data.select_dtypes(exclude=[np.number])
numeric_data = numeric_data.fillna(numeric_data.median())
categorical_data = categorical_data.fillna('Unknown')

# Combine numeric and categorical variables back to a single data frame
data = pd.concat([numeric_data, categorical_data], axis=1)

# DESCRIPTIVE STATISTICS
## Table 0: "Summary of Maternal Age, Gravidity, and Gestational Age"
selected_features = ['AGE', 'GRAVIDA', 'GestationalAge']
means = data[selected_features].mean()
stds = data[selected_features].std()

# Calculate the bootstrap 95% confidence interval for each feature's mean
conf_ints = {feature: tuple(np.percentile([resample(data[feature]).mean() for _ in range(1000)], [2.5, 97.5])) for feature in selected_features}

df0 = pd.DataFrame({'mean': means, 'std': stds, '95% CI': conf_ints})
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
label_encoder = preprocessing.LabelEncoder()
categorical_columns = data.select_dtypes(include= ['object']).columns
for column in categorical_columns:
    data[column+'_Encoded'] = label_encoder.fit_transform(data[column])

# ANALYSIS
pre_treatment = data[data['PrePost'] == 0]
post_treatment = data[data['PrePost'] == 1]

## Table 1: "Test of change in treatment policy on neonatal treatments"
result_ppv = stats.chi2_contingency(pd.crosstab(data['PrePost'], data['PPV']))
result_endo_suction = stats.chi2_contingency(pd.crosstab(data['PrePost'], data['EndotrachealSuction']))
df1 = pd.DataFrame({
    'Treatment': ['PPV', 'EndotrachealSuction'],
    'Chi2 Statistic': [result_ppv.statistic, result_endo_suction.statistic],
    'p-value': [result_ppv.pvalue, result_endo_suction.pvalue]
})
df1.set_index('Treatment', inplace=True)
df1.to_pickle('table_1.pkl')

## Table 2: "Test of change in treatment policy on neonatal outcomes"
result_length_stay = stats.ttest_ind(pre_treatment['LengthStay'], post_treatment['LengthStay'])
result_apgar1 = stats.ttest_ind(pre_treatment['APGAR1'], post_treatment['APGAR1'])
result_apgar5 = stats.ttest_ind(pre_treatment['APGAR5'], post_treatment['APGAR5'])
df2 = pd.DataFrame({
    'Outcome': ['Length Of Stay', 'APGAR1 Score', 'APGAR5 Score'],
    'T-Statistic': [result_length_stay.statistic, result_apgar1.statistic, result_apgar5.statistic],
    'p-value': [result_length_stay.pvalue, result_apgar1.pvalue, result_apgar5.pvalue]
})
df2.set_index('Outcome', inplace=True)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Pregnancies (total number)': data['GRAVIDA'].sum(),         
    'Maternal Diabetes (total number)': data['MaternalDiabetes'].sum(),
    'Fetal Distress (total number)': data['FetalDistress'].sum(),
    'Respiratory Reason for Admission (total number)': data['RespiratoryReasonAdmission'].sum(),
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

