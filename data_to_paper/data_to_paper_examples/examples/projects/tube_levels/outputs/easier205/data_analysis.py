
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from statsmodels.stats.outliers_influence import summary_table
import statsmodels.formula.api as sm

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# There's no missing or undefined data
# No standardization or column modifications are needed

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of height and age stratified by sex"
df0 = df.groupby('sex')[['ht', 'age_c']].agg({'mean', 'std', 'count'}).round(2)
# Convert index to string to give meaningful labels for sex group
df0.index = df0.index.map({0: 'female', 1: 'male'})
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# Data doesn't require further preprocessing    

# ANALYSIS
# Table 1: "Comparison of Mean Squared Errors from Height and Age-Based Models"
height_formula = df['ht'] / 10 + 5
age_formula = np.where(df['age_c'] < 0.5, 9, 
                np.where(df['age_c'] < 1, 10, 
                np.where(df['age_c'] < 2, 11, 12 + (df['age_c'] * 0.5 / 365.25))))
height_MSE = mean_squared_error(df['tube_depth_G'], height_formula)
age_MSE = mean_squared_error(df['tube_depth_G'], age_formula)
df1 = pd.DataFrame({"MSE": [height_MSE, age_MSE]}, 
                   index=["Height Formula", "Age Formula"])
df1.to_pickle('table_1.pkl')

# Table 2: "Statistical Comparison of Residuals of the Height and Age Formula-Based Models"
height_residuals = height_formula - df['tube_depth_G']
age_residuals = age_formula - df['tube_depth_G']
ttest_rel = stats.ttest_rel(height_residuals, age_residuals)
df2 = pd.DataFrame({"Statistics": ['t-statistic', 'p-value'], 
                    "Values": [ttest_rel.statistic, ttest_rel.pvalue]})
df2.set_index('Statistics', inplace=True)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0], 
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
