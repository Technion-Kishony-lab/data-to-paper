
# IMPORT
import pandas as pd
import numpy as np
import pickle
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split, cross_validate, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.exceptions import ConvergenceWarning
from scipy.stats import ttest_rel
import warnings
from sklearn.metrics import mean_squared_error
from math import sqrt

# Supress undesired warnings
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
X = data[['sex', 'age_c', 'ht', 'wt']]
y = data['tube_depth_G']

# Transform sex variable into dummy variable
column_transformer = ColumnTransformer([("one_hot", OneHotEncoder(drop="first"), ["sex"])], remainder="passthrough")
X = column_transformer.fit_transform(X)

# Split data in train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

df_test = data.loc[y_test.index]

# ANALYSIS 
## Table 1: "Comparison of Machine-Learning Models Performance"
pipe_rf = Pipeline([("scl", StandardScaler()), ("reg", RandomForestRegressor(random_state=42))])
pipe_en = Pipeline([("scl", StandardScaler()), ("reg", ElasticNet(random_state=42, max_iter=10000))])
pipe_svm = Pipeline([("scl", StandardScaler()), ("reg", SVR())])
pipe_nn = Pipeline([("scl", StandardScaler()), ("reg", MLPRegressor(random_state=42, max_iter=5000))])

grid_params_rf = [{"reg__n_estimators": [10, 100], "reg__max_depth": [None, 5]}]
grid_params_en = [{"reg__alpha": [0.001, 0.1, 1], "reg__l1_ratio": [0, 0.5, 1]}]
grid_params_svm = [{"reg__C": [0.1, 1, 10], "reg__epsilon": [0.1, 0.2, 0.3]}]
grid_params_nn = [{"reg__hidden_layer_sizes": [(10,), (20,), (50, 50)], "reg__alpha": [0.0001, 0.001, 0.01]}]

grid_rf = GridSearchCV(estimator=pipe_rf, param_grid=grid_params_rf, scoring='neg_mean_squared_error', cv=10, n_jobs=-1) 
grid_en = GridSearchCV(estimator=pipe_en, param_grid=grid_params_en, scoring='neg_mean_squared_error', cv=10, n_jobs=-1)
grid_svm = GridSearchCV(estimator=pipe_svm, param_grid=grid_params_svm, scoring='neg_mean_squared_error', cv=10, n_jobs=-1)
grid_nn = GridSearchCV(estimator=pipe_nn, param_grid=grid_params_nn, scoring='neg_mean_squared_error', cv=10, n_jobs=-1)

pipe_dict = {0: 'Random Forest', 1: 'Elastic Net', 2: 'SVM', 3: 'Neural Network'}
grid_dict = {0: grid_rf, 1: grid_en, 2: grid_svm, 3: grid_nn}
ml_predictions = {}

df1 = pd.DataFrame(columns=["Model", "Mean_Squared_Error", "Std_Error"])

for idx, grid in grid_dict.items():
    grid.fit(X_train, y_train)
    
    cv_results = cross_validate(grid, X_train, y_train, scoring='neg_mean_squared_error', cv=10, return_train_score=True)
    df1.loc["ML_" + pipe_dict[idx]] = [pipe_dict[idx], -grid.score(X_test, y_test), np.sqrt(np.std(-cv_results['test_score']))]
    
    ml_predictions[pipe_dict[idx]] = grid.predict(X_test)
df1.to_pickle('table_1.pkl')

## Table 2: "Comparison of Formula-Based Models Performance"
ages = np.array(df_test["age_c"])
heights = np.array(df_test["ht"])
tube_ids = np.array(df_test["tube"])
depths = y_test.to_numpy()

height_model_ottd = heights/10 + 5
age_model_ottd = np.where(ages < 0.5, 9, np.where(ages < 1, 10, np.where(ages < 2, 11, 12 + ages*0.5)))
id_model_ottd = 3 * tube_ids

formulas_predictions = {
    "Height-Model": height_model_ottd,
    "Age-Model": age_model_ottd,
    "ID-Model": id_model_ottd
}

mse_formulas = [mean_squared_error(formulas_predictions[model], depths) for model in ["Height-Model", "Age-Model", "ID-Model"]]
rmse_formulas = [sqrt(mse) for mse in mse_formulas]

df2 = pd.DataFrame({"Model": ["Height-Model", "Age-Model", "ID-Model"], "Mean_Squared_Error": mse_formulas, "Root_Mean_Squared_Error": rmse_formulas}, columns=["Model", "Mean_Squared_Error", "Root_Mean_Squared_Error"])
df2.index = ["Formula_" + model for model in ["Height", "Age", "ID", ]]
df2.to_pickle('table_2.pkl')

## Table 3: "Comparison of Models based on Hypothesis Testing"
test_results = []
for ml_model in ml_predictions.keys():
    for formula_model in formulas_predictions.keys():
        test_result = ttest_rel(ml_predictions[ml_model], formulas_predictions[formula_model])
        test_results.append({"ML Model": ml_model, "Formula Model": formula_model, 
                             "t-stat": test_result.statistic, "p-value": test_result.pvalue})

df3 = pd.DataFrame(test_results, columns=["ML Model", "Formula Model", "t-stat", "p-value"])
df3.index = ["Test_" + str(i) for i in range(len(df3))]
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS 
additional_results = {
    "total_observations": len(data),
    "random_forest_best_params": grid_rf.best_params_,
    "elastic_net_best_params": grid_en.best_params_,
    "svm_best_params": grid_svm.best_params_,
    "nn_best_params": grid_nn.best_params_
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
