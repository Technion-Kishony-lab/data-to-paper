

# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from scipy.stats import ttest_ind
import warnings
import pickle

# Ignore known warnings
warnings.filterwarnings("ignore")

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics are needed.

# PREPROCESSING 
# No preprocessing is needed, because the features are already numerical and have no missing values.

# ANALYSIS
features = df[['sex', 'age_c', 'ht', 'wt']]
target = df['tube_depth_G']

X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=1)

sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

models = {'Random Forest': RandomForestRegressor(), 
          'Elastic Net': ElasticNet(), 
          'Support Vector Machine': SVR(),
          'Neural Network': MLPRegressor()}

parameters = {'Random Forest': {'n_estimators': [100, 200, 300]}, 
              'Elastic Net': {'alpha': [0.1, 1, 10, 100]}, 
              'Support Vector Machine': {'C': [0.1, 1, 10]},
              'Neural Network': {'hidden_layer_sizes': [(50,), (50, 50)]}}

residuals_ML = []
model_names_ML = []

for model_name, model in models.items():
    grid_search = GridSearchCV(estimator=model, param_grid=parameters[model_name])
    grid_search.fit(X_train, y_train)
    y_pred = grid_search.predict(X_test)
    residuals_ML.append(np.mean((y_test - y_pred) ** 2))
    model_names_ML.append(model_name)

# Table 1: Comparison of mean squared residuals for each Machine Learning Models
df_ML = pd.DataFrame(residuals_ML, index=model_names_ML, columns=["Mean Squared Residuals"])
df_ML.to_pickle('table_1.pkl')

ht_model_preds = df['ht'] / 10 + 5
id_model_preds = 3 * df['tube']
age_model_preds = df['age_c'].apply(lambda x: 9 if x < 0.5 else (10 if x < 1 else (11 if x < 2 else 12 + x*0.5)))

formula_models = [ht_model_preds, id_model_preds, age_model_preds]
formula_names = ['Height Model', 'ID Model', 'Age Model']

residuals_formula = []
for preds in formula_models:
    residuals_formula.append(np.mean((df['tube_depth_G'] - preds) ** 2))

# Table 2: Comparison of mean squared residuals for each Formula-Based Models
df_formula = pd.DataFrame(residuals_formula, index=formula_names, columns=["Mean Squared Residuals"])
df_formula.to_pickle('table_2.pkl')

# Perform t-test comparing mean squared residuals of the Machine Learning models to the residuals of our Formula-Based models
t_test_result = ttest_ind(residuals_ML, residuals_formula)

# Table 3: T-test comparing Machine Learning and Formula-based Models
df_ttest = pd.DataFrame({'Statistic': [t_test_result.statistic], 'P-value': [t_test_result.pvalue]}, index=['Comparison of Machine Learning vs. Formula-based Models'])
df_ttest.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0]
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)

