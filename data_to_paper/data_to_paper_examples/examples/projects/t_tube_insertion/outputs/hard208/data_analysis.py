
# IMPORT
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed

# PREPROCESSING
# No preprocessing is needed

# ANALYSIS
features = ['sex', 'age_c', 'ht', 'wt']
target = 'tube_depth_G'

# Split the data
X_full_train, X_test, y_full_train, y_test = train_test_split(data.drop(target, axis=1), data[target], test_size=0.2, random_state=42)

# Creating Machine learning Models
models = [RandomForestRegressor(), ElasticNet(), SVR(), MLPRegressor(max_iter=2000)]
model_names = ['Random Forest', 'Elastic Net', 'Support Vector Machine', 'Neural Network']

# Hyperparameters
param_grids = [{'n_estimators':[50, 100, 200], 'max_depth':[None, 5, 20], 'min_samples_split':[2, 5, 10]},
               {'alpha': [0.1, 0.5, 1.0], 'l1_ratio': [0.1, 0.5, 1.0]},
               {'C': [0.1, 1, 10], 'epsilon': [0.1, 0.2]},
               {'hidden_layer_sizes': [(50,), (100,), (50, 50)], 'activation': ['identity','logistic']}]

# Create dataframe for squared residuals of machine learning models and formula based models
df1 = pd.DataFrame(index = model_names + ['Height Formula', 'Age Formula', 'ID Formula'])
predictions = []

# Machine learning models and hyperparameters tuning
X_train = X_full_train[features]  # training only with model features
for model, params in zip(models, param_grids):
    grid = GridSearchCV(model, params, cv=5)
    grid.fit(X_train, y_full_train)
    y_pred = grid.predict(X_test[features])
    residuals = (y_test - y_pred) ** 2
    predictions.append(residuals)

# Height Formula
height_formula = X_test['ht'] / 10 + 5
residuals_height = (y_test - height_formula) ** 2
predictions.append(residuals_height)

# Age Formula
age_formula = X_test.apply(lambda row: 9 if row['age_c'] < 0.5 else 10 if row['age_c'] < 1 else 11 
                           if row['age_c'] < 2 else 12 + row['age_c'] * 0.5, axis = 1)
residuals_age = (y_test - age_formula) ** 2
predictions.append(residuals_age)

# ID Formula
id_formula = 3 * X_test['tube']
residuals_ID = (y_test - id_formula) ** 2
predictions.append(residuals_ID)

# Table 1: Mean squared residuals for ML and Formula-based models
df1["Mean Squared Residuals"] = [pred.mean() for pred in predictions]

df1.to_pickle('table_1.pkl')

# Perform Paired T-test
test_results = []
for i in range(len(models)):
    for j in range(len(models),len(models) + 3):
        test_result = ttest_rel(predictions[i], predictions[j])
        test_results.append(test_result.pvalue)

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data), 
 'P-values of T-tests': test_results
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
