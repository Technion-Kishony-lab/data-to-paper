
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistical analysis of patient data stratified by sex"
df0 = df.groupby('sex')[['age_c', 'ht', 'wt', 'tube_depth_G']].mean()
df0.index = df0.index.map({0: 'Female', 1: 'Male'})
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# Get dummy variables for sex
df['male'] = pd.get_dummies(df['sex'], drop_first=True)

# ANALYSIS
# Table 1: "Comparison of Residual Squared Errors from Machine Learning and Formula-Based Models"
X = df[['male', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=123)

models = {
    "Random Forest": RandomForestRegressor(random_state=123),
    "Elastic Net": ElasticNet(random_state=123),
    "Support Vector Machine": SVR(),
    "Neural Network": MLPRegressor(random_state=123, max_iter=2000)
}

results = []
for ml_name, model in models.items():
    model.fit(X_train, y_train)
    ml_y_pred = model.predict(X_test)
    ml_residuals = y_test - ml_y_pred

    df_test = df.loc[X_test.index]
    height_formula = df_test['ht'] / 10 + 5
    age_formula = np.where(df_test['age_c']<0.5,9,np.where(df_test['age_c']<1,10,np.where(df_test['age_c']<2,11,12+(df_test['age_c']-2)*0.5)))
    id_formula = df_test['tube'] * 3

    formula_methods = {"Height Formula": height_formula, "Age Formula": age_formula, "ID Formula": id_formula}

    for formula_name, formula_method in formula_methods.items():
        formula_residuals = y_test - formula_method
        test_results = ttest_rel(ml_residuals, formula_residuals)        
        results.append([ml_name, formula_name, mean_squared_error(y_test, ml_y_pred), mean_squared_error(y_test, formula_method), test_results.statistic, test_results.pvalue])

df1 = pd.DataFrame(results, columns=["ML Method", "Formula Method", "ML MSE", "Formula MSE","t-statistic", "p-value"])
df1.index = ['Comparison ' + str(i) for i in range(1, len(df1) + 1)]
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Num of observations': df.shape[0]
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
