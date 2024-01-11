
# IMPORT
import pandas as pd
import numpy as np
import pickle
import warnings
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel

# To ignore ConvergenceWarning during model training
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
data['gender'] = data['sex'].map({0: 'female', 1:'male'})  # create a new series
data = pd.get_dummies(data)  # create dummy variables

# ANALYSIS
X = data[['gender_male', 'age_c', 'ht', 'wt']]
y = data['tube_depth_G']
tube = data['tube']

X_train, X_test, y_train, y_test, tube_train, tube_test = train_test_split(X, y, tube, test_size=0.3, random_state=42)

ml_models = {'Random Forest': RandomForestRegressor(), 'Elastic Net': ElasticNet(), 'SVM': SVR(), 'Neural Network': MLPRegressor(max_iter=1000)}
formula_predictions = [X_test['ht'] / 10 + 5, 9+np.clip(X_test['age_c'], 0, 4) + 0.5 * np.clip(X_test['age_c'] - 2, 0, np.inf), 3*tube_test]
formula_names = ['Height', 'Age', 'ID']

table1 = {}
for model in ml_models:
    regressor = ml_models[model]
    regressor.fit(X_train, y_train)
    y_pred = regressor.predict(X_test)
    table1[model] = mean_squared_error(y_test, y_pred)
    
df1 = pd.DataFrame.from_dict(table1, orient='index', columns=['Mean Squared Error']) 
df1.to_pickle('table_1.pkl') 

table2 = {}
for i in range(len(formula_predictions)):
    table2[formula_names[i]] = mean_squared_error(y_test, formula_predictions[i]) 

df2 = pd.DataFrame.from_dict(table2, orient='index', columns=['Mean Squared Error'])
df2.to_pickle('table_2.pkl')

p_values = {}
for model1 in table1:
    for i in range(len(formula_predictions)):
        ttest_result = ttest_rel(y_test - ml_models[model1].predict(X_test), y_test - formula_predictions[i])
        p_values[model1 + ' vs ' + formula_names[i]] = ttest_result.pvalue

df3 = pd.DataFrame.from_dict(p_values, orient='index', columns=['p-values'])
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data)
}
for model in ml_models:
    additional_results[model + ' R-squared'] = ml_models[model].score(X_test, y_test)

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
