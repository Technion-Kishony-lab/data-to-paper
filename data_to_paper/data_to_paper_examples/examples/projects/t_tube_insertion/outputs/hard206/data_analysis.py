

# IMPORT
import pickle
from scipy import stats
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error

# LOAD DATA
data = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# Standardization of numeric values into same-unit values
scaler = StandardScaler()
data_std = scaler.fit_transform(data[['age_c', 'ht', 'wt']])
X = data[['sex']]
X = pd.concat([X, pd.DataFrame(data_std, columns=['age_c', 'ht', 'wt'])], axis=1)
y = data['tube_depth_G']

# ANALYSIS
# Splitting Data 
# Train test split for model validation
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=0.3)

# Machine Learning Models MSE
estimators = {'Random Forest': RandomForestRegressor(), 
         'Elastic Net': ElasticNet(), 
         'SVM': SVR(), 
         'Neural Net': MLPRegressor(max_iter=1000)}

ml_models = []
ml_mse = []
ml_preds = []
for model, estimator in estimators.items():
    estimator.fit(X_train, y_train)
    preds = estimator.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    ml_models.append(model)
    ml_mse.append(mse)
    ml_preds.append(preds)

# Select the best ML model
best_ml_index = ml_mse.index(min(ml_mse))
best_ml_model = ml_models[best_ml_index]
best_ml_mse = ml_mse[best_ml_index]
best_ml_preds = ml_preds[best_ml_index]

# Formula Based Models MSE
# 1. Based on height
prediction_height_based = X_test['ht'] / 10 + 5
mse_height_based = mean_squared_error(y_test, prediction_height_based)

# 2. Based on age
prediction_age_based = 9 + 0.5 * (X_test['age_c'] - 0.5).clip(lower=0)
mse_age_based = mean_squared_error(y_test, prediction_age_based)

# 3. Based on Tube Id
prediction_id_based = 3 * data.loc[X_test.index, 'tube']
mse_id_based = mean_squared_error(y_test, prediction_id_based)

formula_models = ['Height Based', 'Age Based', 'ID Based']
formula_mse = [mse_height_based, mse_age_based, mse_id_based]
formula_preds = [prediction_height_based, prediction_age_based, prediction_id_based]


# Dataframe for scientific table 1
df1 = pd.DataFrame({
    'model': [best_ml_model] + formula_models,
    'mse': [best_ml_mse] + formula_mse
}, index=['ML Model', 'Height Formula-Based Model', 'Age Formula-Based Model', 'ID Formula-Based Model'])

df1.to_pickle('table_1.pkl')

# Performing paired ttest
t_stats, p_vals = [], []
for preds in formula_preds:
    residuals_ml = y_test - best_ml_preds
    residuals_formula = y_test - preds
    test_result = stats.ttest_rel(residuals_ml, residuals_formula)
    t_stats.append(test_result.statistic)
    p_vals.append(test_result.pvalue)

# Dataframe for scientific table 2
df2 = pd.DataFrame({
    'model_pair': [f'{best_ml_model} vs {model}' for model in formula_models],
    't_stat': t_stats,
    'p_val': p_vals
}, index=['Pair 1', 'Pair 2', 'Pair 3'])

df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
# Store additional results in a dictionary for use in the paper.
additional_results = {
 'Number of observations': len(data),
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
