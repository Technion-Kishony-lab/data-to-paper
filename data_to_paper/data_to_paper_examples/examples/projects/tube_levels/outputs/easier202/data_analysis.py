
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
import pickle

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of height and age stratified by sex"
grouped = df.groupby("sex")
df_sex_means = grouped[["ht", "age_c"]].mean()
df_sex_std = grouped[["ht", "age_c"]].std()
df0 = pd.concat([df_sex_means, df_sex_std], axis=1)
df0.columns = ['mean_ht', 'mean_age_c', 'std_ht', 'std_age_c'] 
df0.index = df0.index.astype('str')  # convert index to string
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because the data is already clean and does not contain any categorical variables.

# ANALYSIS
# Table 1: "Comparison of actual OTTD measurements and predictions from the height and age models"
# Height Formula-based Model
df['height_model'] = df['ht'] / 10 + 5

# Age Formula-based Model
df.loc[df['age_c'] < 0.5, 'age_model'] = 9
df.loc[(df['age_c'] >= 0.5) & (df['age_c'] < 1), 'age_model'] = 10
df.loc[(df['age_c'] >= 1) & (df['age_c'] < 2), 'age_model'] = 11
df.loc[df['age_c'] >= 2, 'age_model'] = 12 + df['age_c']*0.5

# Calculate the mean squared residuals for the two models
height_model_msr = np.mean((df['tube_depth_G'] - df['height_model'])**2)
age_model_msr = np.mean((df['tube_depth_G'] - df['age_model'])**2)

df1 = pd.DataFrame({'Height model': [height_model_msr], 'Age model': [age_model_msr]}, index=['Mean Squared Residuals'])
df1.to_pickle('table_1.pkl')

# Run the paired t-test on the residuals
ttest_rel_result = stats.ttest_rel(df['tube_depth_G'] - df['height_model'], df['tube_depth_G'] - df['age_model'])

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0],  
 'Results of paired t-test on residuals': {
     'statistic': ttest_rel_result.statistic,
     'p-value': ttest_rel_result.pvalue
     }
}
with open('additional_results.pkl', 'wb') as f:
   pickle.dump(additional_results, f)
   
# END OF CODE
