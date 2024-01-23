
# IMPORT
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from scipy import stats
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of the dataset, stratified by sex"
df0 = df.groupby('sex').agg(['mean', 'std'])
df0.index = ['female', 'male']
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed.

# ANALYSIS
## Table 1: "Height Formula-based Model Performance"
df1 = df.copy()
df1['predicted_OTTD_formula'] = df1['ht'] / 10 + 5
df1['residuals_formula'] = df1['tube_depth_G'] - df1['predicted_OTTD_formula']

## Table 2: "Random Forest Model Performance"
X = df[['sex', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0) 

rf_reg = RandomForestRegressor(n_estimators=20, random_state=0) 
rf_reg.fit(X_train, y_train) 
y_pred = rf_reg.predict(X_test)

residuals_rf = y_test - y_pred

## Table 3: "Comparison between the Height Formula and RF Model"
# perform the t-test
ttest_res = stats.ttest_ind(df1['residuals_formula'], residuals_rf)
# create a DataFrame
df3 = pd.DataFrame({'t_statistic': [ttest_res.statistic], 'p_value': [ttest_res.pvalue]})
df3.index = ['Hypothesis Test']
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'number_of_observations': len(df),
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
