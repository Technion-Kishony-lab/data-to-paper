
# IMPORT
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel


# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')


# DATASET PREPARATIONS
# No dataset preparations are needed.


# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.


# PREPROCESSING
features = df[['sex','age_c','ht','wt']]
target = df['tube_depth_G']


# SPLIT DATA
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=0)


# ML MODELS
models = {
    'RF':RandomForestRegressor(),
    'EN':ElasticNet(),
    'SVM':SVR(),
    'NN':MLPRegressor()
}

ml_predictions = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    ml_predictions[name] = y_pred


# FORMULA-BASED MODELS
df_test = pd.concat([X_test, y_test], axis=1)
df_test['HF'] = df_test['ht'] / 10 + 5
df_test['AF'] = 12 + (df_test['age_c'] / 2)
df_test['IDF'] = 3 * df_test['ht'] / 10 

formula_predictions = df_test[['HF', 'AF', 'IDF']].values


# ANALYSIS
df1 = pd.DataFrame()
for name in models.keys():
    df1[name] = [mean_squared_error(y_test, ml_predictions[name])]

for col in ['HF', 'AF', 'IDF']:
    df1[col] = [mean_squared_error(df_test['tube_depth_G'], df_test[col])]

df1.index = ['MSE']
df1.to_pickle('table_1.pkl') # Table 1: "Mean squared residuals for each model"

data = [] # interim list to hold the data
for model in models.keys():
    for formula in ['HF', 'AF', 'IDF']:
        ttest = ttest_rel(np.square(ml_predictions[model] - y_test), np.square(df_test[formula] - df_test['tube_depth_G']))
        data.append([model, formula, ttest.pvalue]) # append the data

df2 = pd.DataFrame(data, columns=['ML Model', 'Formula Model', 'p_value'])
df2.index = ['Test_' + str(i) for i in df2.index]
df2.to_pickle('table_2.pkl') # Table 2: "Paired t-test results between each ML model and formula-based model"

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),
    'Number of ML models': len(models),
    'Number of formula-based models': 3
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
