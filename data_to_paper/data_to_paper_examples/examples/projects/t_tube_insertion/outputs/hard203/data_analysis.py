
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_ind
import pickle
import warnings
warnings.filterwarnings('ignore')

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of patient's sex, age, height, weight and Optimal Tracheal Tube Depth"
df0 = data[['sex', 'age_c', 'ht', 'wt', 'tube_depth_G']].describe().loc[['mean', 'std']]
df0.to_pickle('table_0.pkl')

# PREPROCESSING
y = data['tube_depth_G']
X = data.drop(columns=['tube', 'tube_depth_G'])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ANALYSIS
# Table 1: "Performance comparison among Machine Learning models and formula-based models"
ml_models = {
    'Random Forest': RandomForestRegressor(),
    'Elastic Net': ElasticNet(),
    'Support Vector Machine': SVR(),
    'Neural Network': MLPRegressor(max_iter=1000)
}

ml_results = {}
ml_preds = {}

for model_name, model in ml_models.items():
    model.fit(X_train_scaled, y_train)
    predictions = model.predict(X_test_scaled)
    squared_residues = mean_squared_error(y_test, predictions)
    ml_results[model_name] = squared_residues
    ml_preds[model_name] = predictions

formula_based_results = {
    'Height Formula': mean_squared_error(y_test, X_test['ht'] / 10 + 5),
    'Age Formula': mean_squared_error(y_test, X_test['age_c']),
    'ID Formula': mean_squared_error(y_test,  X_test['wt'] * 3)
}

formula_preds = {
    'Height Formula': X_test['ht'] / 10 + 5,
    'Age Formula': X_test['age_c'],
    'ID Formula': X_test['wt'] * 3
}

ml_results.update(formula_based_results)

df1 = pd.DataFrame.from_dict(ml_results, orient='index', columns=['Squared Residues'])
for ml_method, pred in ml_preds.items():
    for formula_method, formula_pred in formula_preds.items():
        ttest_res = ttest_ind(pred, formula_pred)
        df1.loc[ml_method, f'p-value vs {formula_method}'] = ttest_res.pvalue

df1 = df1.fillna('-')
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data), 
 'Total number of test observations': len(X_test)
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
