
# IMPORT
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNetCV
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold, cross_val_score
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
import numpy as np
import pickle

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed


# DESCRIPTIVE STATISTICS
## Table 0: "Summary statistics of age and height"
df0 = data.groupby('sex')[['age_c', 'ht']].agg(['mean', 'std'])
df0.columns = ['_'.join(col) for col in df0.columns.values]
df0.index = ['Female', 'Male']
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because all variables are in numerical format

# ANALYSIS
## Table 1: "Comparison of predictive power of different models"
features = data[['sex', 'age_c', 'ht', 'wt']]
target = data['tube_depth_G']

models = [ElasticNetCV(cv=5), RandomForestRegressor(), SVR(), MLPRegressor(hidden_layer_sizes=(50,), max_iter=1000)]
model_names = ['ElasticNet', 'RandomForest', 'SVM', 'NeuralNetwork']

# Initialize KFold
cv = KFold(5, random_state=1, shuffle=True)

results = []
hyperparams = {}
for model, name in zip(models, model_names):
    model.fit(features, target)
    mse = mean_squared_error(target, model.predict(features))
    hyperparams[name] = model.get_params()
    
    # Nested cross-validation for t-test
    scores = cross_val_score(model, features, target, cv=cv, scoring='neg_mean_squared_error')
    t_results = stats.ttest_1samp(scores, mse)
    results.append((name, mse, t_results.pvalue))

df1 = pd.DataFrame(results, columns=['Model', 'Mean_Squared_Error', 'p_value'])
df1['index'] = ['Model_1', 'Model_2', 'Model_3', 'Model_4']
df1.set_index('index', inplace=True)
df1 = df1.round(3)
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {'Total number of observations': len(data), 'Model Hyperparameters': hyperparams}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
