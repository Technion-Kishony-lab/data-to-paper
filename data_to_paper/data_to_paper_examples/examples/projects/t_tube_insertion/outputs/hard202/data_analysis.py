
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle
import warnings

# To ignore warning related to more iteration needed for convergence in MLPRegressor
warnings.filterwarnings('ignore')

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of height and tube_depth_G stratified by sex"
df0 = df.groupby('sex').agg({'tube': ['mean', 'min', 'max'], 'tube_depth_G': ['mean', 'min', 'max']})
df0.index = df0.index.map({0:'female', 1:'male'})
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# Creating dummies for 'sex' column
df = pd.get_dummies(df, columns=['sex'], drop_first=True)

# Splitting data into train and test datasets
X_train, X_test, y_train, y_test = train_test_split(df.drop('tube_depth_G', axis=1), df['tube_depth_G'], test_size=0.2, random_state=42)

# ANALYSIS
models = [RandomForestRegressor(), ElasticNet(), SVR(), MLPRegressor(max_iter=1000)]
model_names = ["Random Forest", "Elastic Net", "Support Vector Machine", "Neural Network"]

residuals = []
names = []

for model, name in zip(models, model_names):
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    residuals.append(preds - y_test)
    names.append(name)

# Adding the tube_depth_G column to the test set
X_test['tube_depth_G'] = y_test

# Formula-based Model Calculations
# Calculating for test set only
X_test['height_formula'] = X_test['ht'] / 10 + 5
X_test['age_formula'] = X_test['age_c'].apply(lambda x: 9 if x < 0.5 else 10 if x < 1 else 11 if x < 2 else 12 + 0.5 * x)
X_test['id_formula'] = 3 * X_test['tube']

for formula in ['height_formula', 'age_formula', 'id_formula']:
    residuals.append(X_test[formula] - X_test['tube_depth_G'])
    names.append(formula.replace('_formula', ' formula-based model'))

# Table 1: "Comparison of Residual sum of squares (RSS) of each model"
residual_sum_squares = [np.sum(np.square(res)) for res in residuals]
p_values = [ttest_rel(res, np.zeros_like(res)).pvalue for res in residuals]

df1 = pd.DataFrame({'Model': names, 'Residual Sum of Squares': residual_sum_squares, 'p-value': p_values})
df1.set_index('Model', inplace=True)
df1.index.name = None
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
     'Total number of observations': df.shape[0], 
     'Total number of test observations': X_test.shape[0]
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
