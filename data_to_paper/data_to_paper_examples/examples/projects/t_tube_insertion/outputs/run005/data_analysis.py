
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import warnings
import pickle


# Ignore warnings
warnings.filterwarnings('ignore')

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed, because all data columns are numerical and do not require transformation.

# ANALYSIS

## Table 1: "Comparison of mean squared residuals of predicted OTTD by each machine-learning model and each formula-based model"

# Prepare features and target
features = df[['sex', 'age_c', 'ht', 'wt']]
target = df['tube_depth_G']

# Split data
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

# Create formula-based predictions
df_test = df.iloc[X_test.index]
df_test['ht_formula'] = df_test['ht'] / 10 + 5
df_test['age_formula'] = np.select([df_test['age_c'] < 0.5, df_test['age_c'] < 1, df_test['age_c'] < 2, df_test['age_c'] >= 2],
                                   [9, 10, 11, 12 + df_test['age_c'] * 0.5])
df_test['id_formula'] = df_test['tube'] * 3

# Compute residuals for formula-based models
residuals = {'height_formula': (df_test['ht_formula'] - y_test)**2,
             'age_formula': (df_test['age_formula'] - y_test)**2,
             'id_formula': (df_test['id_formula'] - y_test)**2}

# Create machine learning models
models = {'Random Forest': (RandomForestRegressor(), {'n_estimators': [10, 50, 100], 'max_depth': [None, 5, 10, 15, 20]}),
          'Elastic Net': (ElasticNet(), {'alpha': [0.1, 0.5, 1, 2, 5], 'l1_ratio': [0, 0.5, 1]}),
          'Support Vector Machine': (SVR(), {'C': [0.1, 1, 10, 100]}),
          'Neural Network': (MLPRegressor(max_iter=500), {'hidden_layer_sizes': [(50, 50), (100,)], 'activation': ['tanh', 'relu']})
          }
# Hyperparameter tuning and prediction for each model
for name, (model, params) in models.items():
    gs = GridSearchCV(model, params)
    gs.fit(X_train, y_train)
    predictions = gs.predict(X_test)
    residuals[name] = (predictions - y_test) ** 2
    models[name] = (gs.best_estimator_, gs.best_params_, mean_squared_error(y_test, predictions))

# Running t-tests for residuals
t_test_results = {}
for mdl in models.keys():
    for formula in ['height_formula', 'age_formula', 'id_formula']:
        t_test_result = ttest_rel(residuals[mdl], residuals[formula])
        t_test_results[f'{mdl} vs {formula}'] = [residuals[mdl].mean(), residuals[formula].mean(), t_test_result.pvalue]

# Prepare DataFrame for Table 1
df1 = pd.DataFrame(t_test_results, index=['ML Mean Sq Residual', 'Formula Mean Sq Residual', 'p-value']).T
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),
    'Observations used for training': len(X_train),
    'Observations used for testing': len(X_test),
}

for name, (model, params, mse) in models.items():
    additional_results[name] = {
        'best_hyperparameters': params,
        'model_mse': mse
    }

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
