
# IMPORT
import pandas as pd
import pickle
from scipy.stats import chi2_contingency
from scipy.stats import ttest_ind

# LOAD DATA
data = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Mean and Std dev of APGAR scores and SNAPPE_II_SCORE stratified by pre and post policy"
columns = ['APGAR1', 'APGAR5', 'SNAPPE_II_SCORE']
grouped_data = data.groupby('PrePost')[columns]
mean = grouped_data.mean().add_suffix('_mean').round(2)
std = grouped_data.std().add_suffix('_std').round(2)
df0 = pd.concat([mean, std], axis=1, sort=False)
df0.index.rename("Group: 0= Pre 2015, 1= Post 2015", inplace=True)
df0.index = df0.index.astype(str) 

df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is needed because our data are already suitable for the analysis.

# ANALYSIS
## Table 1: "Association between treatments and change in policy using Chi-square test"
treatment_columns = ['PPV', 'EndotrachealSuction', 'MeconiumRecovered']
chisq_results = []
for column in treatment_columns:
    contingency = pd.crosstab(data['PrePost'], data[column])
    result = chi2_contingency(contingency)
    chisq_results.append({'Treatment': column, 'Chi2': result.statistic, 'p_value': result.pvalue})
df1 = pd.DataFrame(chisq_results)
df1 = df1.set_index('Treatment').round(2)
df1.to_pickle('table_1.pkl')

## Table 2: "Difference in APGAR scores between pre and post intervention groups using independent t-test"
outcome_columns = ['APGAR1', 'APGAR5']
groups = [data.loc[data['PrePost'] == 0], data.loc[data['PrePost'] == 1]]
ttest_results = []
for column in outcome_columns:
    result = ttest_ind(groups[0][column], groups[1][column], nan_policy='omit')
    ttest_results.append({'Outcome': column, 'T_statistic': result.statistic, 'p_value': result.pvalue})
df2 = pd.DataFrame(ttest_results)
df2 = df2.set_index('Outcome').round(2)
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data),
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
