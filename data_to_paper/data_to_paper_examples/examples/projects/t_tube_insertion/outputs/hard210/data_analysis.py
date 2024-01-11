

# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.exceptions import ConvergenceWarning
import warnings
import pickle

warnings.filterwarnings('ignore', category=ConvergenceWarning)

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed

# PREPROCESSING 
scaler = StandardScaler()
scaled_features = scaler.fit_transform(data[['age_c', 'ht', 'wt']])
df = pd.DataFrame(scaled_features, columns=['age_c', 'ht', 'wt'])
df['sex'] = data['sex']
X = df[['sex', 'age_c', 'ht', 'wt']]
y = data['tube_depth_G']

# ANALYSIS 
# Create the models
models = {
    'Random Forest': RandomForestRegressor(random_state=123),
    'Elastic Net': ElasticNet(random_state=123),
    'SVM': SVR(),
    'Neural Network': MLPRegressor(random_state=123, max_iter=1000)
}

param_grid = {
    'Random Forest': {'n_estimators': [10, 50, 100]},
    'Elastic Net': {'alpha': [0.001, 0.01, 0.1]},
    'SVM': {'C': [0.1, 1, 10]},
    'Neural Network': {'hidden_layer_sizes': [(10,), (50,), (100,)]}
}

residuals = {}

for model_name, model in models.items():
    grid = GridSearchCV(model, param_grid[model_name], cv=5, scoring='neg_mean_squared_error')
    grid.fit(X, y)
    residuals[model_name] = (y - grid.predict(X)) ** 2

df['Height Formula'] = df['ht'] / 10 + 5
df['Age Formula'] = np.where(df['age_c'] < 0.5, 9, np.where(df['age_c'] < 1, 10, np.where(df['age_c'] < 2, 11, 12 + df['age_c'] * 0.5)))
df['ID Formula'] = 3 * data['tube']

for formula in ['Height Formula', 'Age Formula', 'ID Formula']:
    residuals[formula] = (y - df[formula]) ** 2

pvalues = {}

for ml_model in models.keys():
    for formula in ['Height Formula', 'Age Formula', 'ID Formula']:
        ttest = stats.ttest_rel(residuals[ml_model], residuals[formula])
        pvalues[f'{ml_model} versus {formula}'] = ttest.pvalue

_, pvalues_adjusted, _, _ = multipletests(list(pvalues.values()), method='bonferroni')
adjusted_pvalues = dict(zip(pvalues.keys(), pvalues_adjusted))
df1 = pd.DataFrame(list(adjusted_pvalues.items()), columns=['Comparison', 'Adjusted p-value'])
df1.index = [f'Comparison {i+1}' for i in range(df1.shape[0])]
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data)
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

