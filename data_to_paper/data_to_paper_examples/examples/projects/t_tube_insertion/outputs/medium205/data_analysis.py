
# IMPORT
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
## No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Mean and standard deviation of tube, age, height, weight, and tube_depth_G stratified by sex"
df0 = df.groupby('sex').aggregate(['mean', 'std']).rename(index={0: 'female', 1: 'male'})
df0.columns = [' '.join(col).strip() for col in df0.columns.values]
df0.index.name='sex'
df0.to_pickle('table_0.pkl')

# PREPROCESSING
## Creating dummy variables for sex
df = pd.get_dummies(df, columns=['sex'], drop_first=True)

# ANALYSIS
## Create a new column for the formula-based model
df['ht_form'] = df['ht'] / 10 + 5

## Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(df.drop(['tube_depth_G', 'ht_form'], axis=1), df['tube_depth_G'], test_size=0.2, random_state=42)

## Initialize the model
rf_model = RandomForestRegressor(n_estimators=200, max_depth=5, random_state=42)

## Train the model
rf_model.fit(X_train, y_train)

## Making predictions
rf_predictions = rf_model.predict(X_test)
ht_predictions = X_test.ht / 10 + 5

## Comparing ML model residuals and formula-based model residuals
rf_res = y_test - rf_predictions
ht_res = y_test - ht_predictions

## Table 1: "Comparison of residuals between the ML model and formula-based model"
df_res = pd.DataFrame( {'RF_model' : rf_res , 'Height_Formula' : ht_res})
df1 = df_res.aggregate(['mean', 'std']).T
df1['p_val'] = [ttest_rel(rf_res, ht_res).pvalue]*len(df1)
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0],
 'Test sample size': X_test.shape[0],
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
