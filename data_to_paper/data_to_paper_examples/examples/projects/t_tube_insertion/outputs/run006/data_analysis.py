

# IMPORT
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
df.loc[df['age_c'] < 0.5, 'depth_formula_age'] = 9
df.loc[(df['age_c'] >= 0.5) & (df['age_c'] < 1),'depth_formula_age'] = 10
df.loc[(df['age_c'] >= 1) & (df['age_c'] < 2),'depth_formula_age'] = 11 
df.loc[df['age_c'] >= 2,'depth_formula_age'] = 12 + (df['age_c'] * 0.5)
df['depth_formula_height'] = (df['ht'] / 10) + 5
df['depth_formula_tube'] = df['tube'] * 3

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of sex, age, height, weight stratified by sex"
df0 = df[['sex','age_c','ht','wt']].agg(['mean','std','count'])
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# Split data into features and target
X = df[['sex', 'age_c', 'ht', 'wt']]
Y = df['tube_depth_G']

# Split data into training and test sets
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=1)

# ANALYSIS
models = [RandomForestRegressor(random_state=1),
          SVR(kernel='linear'), 
          MLPRegressor(max_iter=500),
          ElasticNet()]

params_list = [{"max_depth": range(1, 4), "n_estimators": [10, 30, 50]},
                {'C': [0.1, 1, 10], 'epsilon': [0.1, 0.2, 0.3]},
                {'alpha': [0.0001, 0.001, 0.01], 'learning_rate': ['constant']},
                {'alpha': [0.1, 1, 2], 'l1_ratio': [0.1, 0.5, 0.7]}]

model_names = ['RandomForest', 'SVM', 'NN', 'ElasticNet']
formulae = ['depth_formula_age', 'depth_formula_height', 'depth_formula_tube']

## Table 1: "Mean Squared Error and p-value for each Machine Learning Model compared with each formula-based method"
df1 = pd.DataFrame(columns=['MSE ML Model', 'MSE Formula', 'p-value'])

for idx, model in enumerate(models):
    grid = GridSearchCV(model, params_list[idx], cv=5, verbose=0)      
    grid.fit(X_train, Y_train)
    best_model = grid.best_estimator_
    predictions = best_model.predict(X_test)
    mse_ml = ((Y_test - predictions) ** 2).mean()
    
    for formula in formulae:
        formula_predictions = df.loc[X_test.index, formula]
        if formula_predictions.isnull().values.any():
            formula_predictions.fillna(formula_predictions.mean(), inplace=True)
        mse_formula = ((Y_test - formula_predictions) ** 2).mean()
        p_value = ttest_rel((Y_test - predictions) ** 2, (Y_test - formula_predictions) ** 2).pvalue
        row_index = model_names[idx] + ' vs ' + formula
        df1.loc[row_index] = [mse_ml, mse_formula, p_value]

df1 = df1.rename_axis('ML Model vs Formula')
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0],
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

