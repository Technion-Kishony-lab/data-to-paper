
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import f_oneway
import warnings
import pickle

warnings.filterwarnings("ignore", category=DeprecationWarning)

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
df = pd.get_dummies(df, columns=['sex'], drop_first=True)

# ANALYSIS

## Table 1: "Comparison of Squared Residuals of Machine Learning Models and Formula-Based Models"
df_train, df_test = train_test_split(df, test_size=0.2, random_state=42)

# Machine Learning Models
ml_models = [RandomForestRegressor(), ElasticNet(), SVR(), MLPRegressor(max_iter=1000)]
ml_names = ["Random Forest", "Elastic Net", "SVM", "Neural Network"]
ml_res = []

for model, name in zip(ml_models, ml_names):
    model.fit(df_train[['age_c', 'ht', 'wt', 'sex_1']], df_train['tube_depth_G'])
    predictions = model.predict(df_test[['age_c', 'ht', 'wt', 'sex_1']])
    residuals = (df_test['tube_depth_G'] - predictions) ** 2
    ml_res.append(residuals)

# Formula-Based Models
df_test['HF'] = df_test['ht'] / 10 + 5
df_test['AF'] = np.select(
    [
        df_test['age_c'].between(0, 0.5), 
        df_test['age_c'].between(0.5, 1), 
        df_test['age_c'].between(1, 2), 
        df_test['age_c'] > 2
    ], 
    [
        9, 
        10, 
        11, 
        12 + df_test['age_c'] * 0.5
    ]
)
df_test['IF'] = 3 * df_test['tube']

for model in ['HF', 'AF', 'IF']:
    residuals = (df_test[model] - df_test['tube_depth_G']) ** 2
    ml_res.append(residuals)

residuals_f_results = f_oneway(*ml_res)

df1 = pd.DataFrame(
    {
        'F Value': residuals_f_results.statistic, 
        'p Value': residuals_f_results.pvalue
    }, 
    index=["Model Comparison"]
)
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
  'Total number of observations': len(df)
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
