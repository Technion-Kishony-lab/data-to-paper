
# IMPORT

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# Remove 'tube' variable from ML features
data_ml = data.drop('tube', axis=1)

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed, because all the variables are numeric and there are no missing values

# Splitting the data for training and testing
X_train, X_test, y_train, y_test = train_test_split(data_ml[['sex', 'age_c', 'ht', 'wt']], data_ml['tube_depth_G'], test_size=0.3, random_state=123)

# ANALYSIS

## Table 1: "Comparison of squared residuals between machine learning models and formula-based models"

# Machine Learning Models
rf = RandomForestRegressor(random_state=1)
en = ElasticNet(random_state=1)
svm = SVR()
nn = MLPRegressor(max_iter=1000, random_state=1)
models = [rf, en, svm, nn]
model_names = ['RandomForest', 'ElasticNet', 'SupportVectorMachine', 'NeuralNetwork']
rf_params = {'n_estimators': [50, 100, 150]}
en_params = {'alpha': [0.1, 0.5, 1], 'l1_ratio': [0.1, 0.5, 1]}
svm_params = {'C': [0.1, 1, 10], 'epsilon': [0.1, 0.2, 0.3]}
nn_params = {'hidden_layer_sizes': [(50,), (100,)], 'activation': ['relu', 'tanh']}
params = [rf_params, en_params, svm_params, nn_params]

squared_residuals_ml = {}
for model, model_name, param in zip(models, model_names, params):
    grid = GridSearchCV(model, param, cv=5)
    grid.fit(X_train, y_train)
    predictions = grid.predict(X_test)
    squared_residuals_ml[model_name] = (y_test - predictions) ** 2

squared_residuals_fb = {}
height_model_predictions = X_test['ht'] / 10 + 5
age_model_predictions = np.where(X_test['age_c'] < 0.5, 9,
                                 np.where(X_test['age_c'] < 1, 10, np.where(X_test['age_c'] < 2, 11,
                                                                           12 + X_test['age_c'] * 0.5)))
# Fix : id_model_predictions now using 'tube' data
id_model_predictions = 3 * data.loc[X_test.index, 'tube']

squared_residuals_fb['height_model'] = (y_test - height_model_predictions) ** 2
squared_residuals_fb['age_model'] = (y_test - age_model_predictions) ** 2
squared_residuals_fb['id_model'] = (y_test - id_model_predictions) ** 2

df1 = pd.DataFrame(index=model_names)
for name, sr in squared_residuals_fb.items():
    p_values = [ttest_rel(sr, v).pvalue for v in squared_residuals_ml.values()]
    df1[name] = p_values

df1.to_pickle('table_1.pkl')

## Table 2: "Mean Squared Residuals for each Model"
mean_squared_residuals_ml = {model_name: np.mean(sr) for model_name, sr in squared_residuals_ml.items()}
mean_squared_residuals_fb = {model_name: np.mean(sr) for model_name, sr in squared_residuals_fb.items()}

residuals_table = {**mean_squared_residuals_ml, **mean_squared_residuals_fb}
df2 = pd.DataFrame(list(residuals_table.items()), columns=['Models', 'Mean Squared Residuals'])
df2.set_index('Models', inplace=True)
df2.index.name = None

df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'squared_residuals_ml': squared_residuals_ml,
    'squared_residuals_fb': squared_residuals_fb,
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

