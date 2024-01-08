
# IMPORT
import pickle
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# No preprocessing is needed, because all features are numerical and there is no missing values.

# ANALYSIS
# Calculate optimal tube depth according to the two formula based models
data['height_model'] = data['ht'] / 10 + 5
data['age_model'] = np.select(
    condlist=[data['age_c'] < 0.5, (0.5 <= data['age_c']) & (data['age_c'] < 1), (1 < data['age_c']) & (data['age_c'] < 2), data['age_c'] > 2],
    choicelist=[9, 10, 11, 12 + data['age_c']*0.5]
)

# Calculate residuals for both models
data['residual_height_model'] = (data['tube_depth_G'] - data['height_model'])**2
data['residual_age_model'] = (data['tube_depth_G'] - data['age_model'])**2

## Table 1: "Square residuals for the Height Model and Age Model"
df1 = data[['residual_height_model', 'residual_age_model']].agg(['mean', 'std'])
df1.to_pickle('table_1.pkl')

# Perform Paired t-test on residuals
ttest_results = ttest_rel(data['residual_height_model'], data['residual_age_model'])

## Table 2: "Paired t-test results for residuals of the two models"
df2 = pd.DataFrame(data={'T-Statistic': [ttest_results.statistic], 'p-value': [ttest_results.pvalue]}, index=['Paired T-Test'])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data)
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
