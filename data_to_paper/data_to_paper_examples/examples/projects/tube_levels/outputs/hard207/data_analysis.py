
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import GridSearchCV
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# Table 0: "Descriptive statistics of age and height stratified by sex"
df0 = df.groupby('sex').agg({'age_c': ['mean', 'std'], 'ht': ['mean', 'std']})
df0.index = ['Female', 'Male']
df0.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed.

# ANALYSIS
X = df[['sex', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1)

models = {
   'Random Forest': RandomForestRegressor(),
   'Elastic Net': ElasticNet(),
   'Support Vector Machine': SVR(),
   'Neural Network': MLPRegressor(max_iter=2000)
}

tuned_models = {}
for model in models.keys():
    tuned_models[model] = GridSearchCV(models[model], {}).fit(X_train, y_train)

predictions = {}
for model in tuned_models.keys():
    predictions[model] = tuned_models[model].predict(X_test)

formula_predictions = {
   'Height Formula': X_test['ht'] / 10 + 5,
   'Age Formula': 12 + np.where(X_test['age_c'] > 2, X_test['age_c'] * 0.5, 0),
   'Tube ID Formula': 3 * df.loc[X_test.index, 'tube']
}

# Statistical test
ml_mse = [mean_squared_error(y_test, predictions[model]) for model in predictions.keys()]
formula_mse = [mean_squared_error(y_test, formula_predictions[model]) for model in formula_predictions.keys()]

ttest_res = stats.ttest_ind(ml_mse, formula_mse)

## Table 1: Overall Performance of Machine Learning Models
mse_model = {model: mean_squared_error(y_test, predictions[model]) for model in predictions.keys()}
df1 = pd.DataFrame.from_dict(mse_model, orient='index', columns=['Mean Squared Error'])
df1.to_pickle('table_1.pkl')

## Table 2: Overall Performance of Formula-Based Models
mse_formula = {model: mean_squared_error(y_test, formula_predictions[model]) for model in formula_predictions.keys()}
df2 = pd.DataFrame.from_dict(mse_formula, orient='index', columns=['Mean Squared Error'])
df2.to_pickle('table_2.pkl')

## Table 3: "Independent t-test: Comparison of ML models vs Formula-Based models"
df3 = pd.DataFrame(
   {
     "t-statistic": [ttest_res.statistic],
     "p-value": [ttest_res.pvalue],
   },
   index=["ML models vs Formula-based models"]
)
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df),
 't-test statistic': ttest_res.statistic,
 't-test p-value': ttest_res.pvalue,
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
 