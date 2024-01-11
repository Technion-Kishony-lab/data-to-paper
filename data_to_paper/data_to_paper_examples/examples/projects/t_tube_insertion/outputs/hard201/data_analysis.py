
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from scipy.stats import wilcoxon
import warnings
import pickle

warnings.filterwarnings('ignore')

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed here.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# The feature 'sex' is a binary variable and does not require encoding.

# ANALYSIS
## Table 1: "Comparing predictive power of ML models vs formula-based models on individual test samples"

# Split data into train and test sets
features = ['sex', 'age_c', 'ht', 'wt']
target = 'tube_depth_G'
X = data[features]
y = data[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

# Initialize models with hyperparameter grid for tuning
models = {
    'Random Forest': {'model': RandomForestRegressor(), 'params': {'n_estimators': [10, 50, 100]}},
    'Elastic Net': {'model': ElasticNet(), 'params': {'alpha': [0.01, 0.1, 1, 10]}},
    'Support Vector Machine': {'model': SVR(), 'params': {'C': [0.1, 1, 10, 100], 'epsilon': [0.01, 0.1, 1, 10]}},
    'Neural Network': {'model': MLPRegressor(max_iter=1000), 'params': {'hidden_layer_sizes': [(10,), (50,), (10, 10), (50,50)], 'activation': ['relu', 'tanh']}}
}

# Formula-based models
def apply_formula(data):
    data['Height Formula'] = data['ht'] / 10 + 5
    data['Age Formula'] = np.select(
        condlist=[data['age_c'] < 0.5, data['age_c'] < 1, data['age_c'] < 2, data['age_c'] >= 2], 
        choicelist=[9, 10, 11, 12 + data['age_c'] * 0.5]
    )
    data['ID Formula'] = 3 * data['tube']
    return data

data = apply_formula(data)

# initialize output table with model names as index
mean_squared_residuals = pd.DataFrame(index=list(models.keys()) + ['Height Formula', 'Age Formula', 'ID Formula'])

# Loop through models and apply grid search
for model_name, model_info in models.items():
    gs = GridSearchCV(model_info['model'], model_info['params'], cv=KFold(n_splits=5))
    gs.fit(X_train, y_train)
    best_model = gs.best_estimator_
    test_preds = best_model.predict(X_test)
    mean_squared_residuals.loc[model_name, 'Error'] = np.mean((test_preds - y_test) ** 2)
    models[model_name]['model'] = best_model # update the model in the models dictionary

# Add formula-based models to output table
for formula in ['Height Formula', 'Age Formula', 'ID Formula']:
    mean_squared_residuals.loc[formula, 'Error'] = np.mean((data.loc[X_test.index, formula] - y_test) ** 2)

mean_squared_residuals.to_pickle('table_1.pkl')

## Table 2: "Wilcoxon signed-rank test comparing the error between ML models and formula models"

res_testing = pd.DataFrame(index=list(models.keys()), columns=['Height Formula p-value', 'Age Formula p-value', 'ID Formula p-value'])

for ml_model in models:
    for formula in ['Height Formula', 'Age Formula', 'ID Formula']:
        result = wilcoxon((models[ml_model]['model'].predict(X_test) - y_test) ** 2, (data.loc[X_test.index, formula] - y_test) ** 2)
        res_testing.loc[ml_model, formula+' p-value'] = result.pvalue

res_testing.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS

additional_results = {
 'Total number of observations': len(data),
 'Number of training samples': len(X_train),
 'Number of test samples': len(X_test)
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
