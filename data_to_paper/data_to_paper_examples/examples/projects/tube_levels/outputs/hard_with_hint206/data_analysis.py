
# IMPORT
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_ind
import pickle
import numpy as np

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed, because all variables are already numerical.

# ANALYSIS
# ML Models
features = data[["sex", "age_c", "ht", "wt"]]
target = data["tube_depth_G"]
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=1)

## Random Forest
rf = RandomForestRegressor()
params = {"n_estimators":[50, 100, 150], "max_depth":[None, 5, 10], "random_state":[1]}
gcv_rf = GridSearchCV(rf, params, cv=5)
gcv_rf.fit(X_train, y_train)
rf_mse = mean_squared_error(y_test, gcv_rf.predict(X_test))

## Elastic Net
en = ElasticNet()
params = {"alpha":[0.1, 0.5, 1], "l1_ratio":[0.2, 0.5, 0.8], "random_state":[1]}
gcv_en = GridSearchCV(en, params, cv=5)
gcv_en.fit(X_train, y_train)
en_mse = mean_squared_error(y_test, gcv_en.predict(X_test))

## SVM
svm = SVR()
params = {"C":[0.5, 1, 2], "epsilon":[0.1, 0.2, 0.3]}
gcv_svm = GridSearchCV(svm, params, cv=5)
gcv_svm.fit(X_train, y_train)
svm_mse = mean_squared_error(y_test, gcv_svm.predict(X_test))

## Neural Network
nn = MLPRegressor(max_iter=1000) # increased max_iter to 1000 to ensure convergence
params = {"hidden_layer_sizes":[(50,), (30, 20)], "random_state":[1]}
gcv_nn = GridSearchCV(nn, params, cv=5)
gcv_nn.fit(X_train, y_train)
nn_mse = mean_squared_error(y_test, gcv_nn.predict(X_test))

# Formula-based Models
## Height Formula
height_formula_mse = mean_squared_error(data["tube_depth_G"], data["ht"] / 10 + 5)

## Age Formula
age_formula_predictions = pd.Series(np.where(data["age_c"] < 0.5, 9, np.where(data["age_c"] < 1, 10, np.where(data["age_c"] == 1, 11, 12 + data["age_c"] * 0.5))))
age_formula_mse = mean_squared_error(data["tube_depth_G"], age_formula_predictions)

## ID Formula
id_formula_mse = mean_squared_error(data["tube_depth_G"], 3 * data["tube"])

## Table 1: "Comparison of mean squared residuals of Machine Learning Models and Formula-based Models"
df1 = pd.DataFrame({
    "Model Type":["Random Forest", "Elastic Net", "SVM", "Neural Network", "Height Formula", "Age Formula", "ID Formula"],
    "MSE":[rf_mse, en_mse, svm_mse, nn_mse, height_formula_mse, age_formula_mse, id_formula_mse]
}, index=(i for i in ["Model " + str(i) for i in range(1, 8)]))
df1.to_pickle('table_1.pkl')

# Pairwise t-tests
rf_ttest = ttest_ind(y_test - gcv_rf.predict(X_test), y_test - (data.loc[X_test.index, "ht"] / 10 + 5))
en_ttest = ttest_ind(y_test - gcv_en.predict(X_test), y_test - (data.loc[X_test.index, "ht"] / 10 + 5))
svm_ttest = ttest_ind(y_test - gcv_svm.predict(X_test), y_test - (data.loc[X_test.index, "ht"] / 10 + 5))
nn_ttest = ttest_ind(y_test - gcv_nn.predict(X_test), y_test - (data.loc[X_test.index, "ht"] / 10 + 5))

## Table 2: "Pairwise comparison of Machine Learning Models and Height-based Formula Model"
df2 = pd.DataFrame({
    "ML Model":["Random Forest", "Elastic Net", "SVM", "Neural Network"],
    "T statistic":[rf_ttest.statistic, en_ttest.statistic, svm_ttest.statistic, nn_ttest.statistic],
    "p-value":[rf_ttest.pvalue, en_ttest.pvalue, svm_ttest.pvalue, nn_ttest.pvalue]
}, index=(i for i in ["ML Model " + str(i) for i in range(1, 5)]))
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(data), 
    'accuracy of random forest model': gcv_rf.score(X_test, y_test), 
    'accuracy of elastic net model': gcv_en.score(X_test, y_test),
    'accuracy of SVM model': gcv_svm.score(X_test, y_test),
    'accuracy of neural network model': gcv_nn.score(X_test, y_test),
    'best parameters of random forest model': gcv_rf.best_params_,
    'best parameters of elastic net model': gcv_en.best_params_,
    'best parameters of SVM model': gcv_svm.best_params_,
    'best parameters of neural network model': gcv_nn.best_params_,
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
