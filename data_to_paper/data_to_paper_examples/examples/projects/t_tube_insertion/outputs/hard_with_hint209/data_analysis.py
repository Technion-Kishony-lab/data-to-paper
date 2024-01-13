
# IMPORT
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed, because all variables are numeric and there is no missing data.

# ANALYSIS
X = df[['sex', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Machine learning models
models = {
    'Random Forest': RandomForestRegressor(),
    'Elastic Net': ElasticNetCV(),
    'Support Vector Machine': SVR(),
    'Neural Network': MLPRegressor(max_iter=1000)
}

# Fit ML models and predict
ml_mse = []
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    ml_mse.append(mse)

# Formula-based models
test_df = df.loc[X_test.index].copy()
test_df['pred_height'] = test_df['ht'] / 10 + 5
test_df['pred_age'] = np.select(
    [test_df['age_c'] < 0.5, test_df['age_c'] < 1, test_df['age_c'] < 2, test_df['age_c'] >= 2], 
    [9, 10, 11, 12 + test_df['age_c'] * 0.5]
)
test_df['pred_id'] = 3 * test_df['tube']

# Calculate MSE for formula-based models
fb_mse = [mean_squared_error(y_test, test_df['pred_height']), 
          mean_squared_error(y_test, test_df['pred_age']), 
          mean_squared_error(y_test, test_df['pred_id'])]
avg_fb_mse = np.mean(fb_mse)

# T-test
t_test_results = ttest_rel(ml_mse, [avg_fb_mse] * 4)

# Save to table_1.pkl
df1 = pd.DataFrame(list(zip(['Random Forest', 'Elastic Net', 'Support Vector Machine', 'Neural Network'], 
                            ml_mse, 
                            [t_test_results.statistic]*4, 
                            [t_test_results.pvalue]*4)), 
                   columns=['Model', 'MSE', 't_stat', 'p_value'])
df1.index = df1.index.map(str)
df1 = df1.set_index('Model')

df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df), 
 'Number of training observations': len(X_train),
 'Number of test observations': len(X_test)
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

