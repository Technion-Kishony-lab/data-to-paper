
# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# No preprocessing is needed, because the variables are already in suitable formats.

# ANALYSIS
## Table 1: "Comparison of p-values from the paired t-test of squared residuals of different machine-learning models and formula-based models"

X = df[["sex", "age_c", "ht", "wt"]].values
y = df["tube_depth_G"].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1)

models_params = [("Random Forest", RandomForestRegressor(), {"n_estimators": [50, 100, 150], "max_depth": [5, 10, 15]}),
                 ("Elastic Net", ElasticNet(), {"alpha": [0.1, 0.5, 1], "l1_ratio": [0.1, 0.5, 1]}),
                 ("Support Vector Machine", SVR(), {"C": [0.1, 1, 10], "gamma": ["scale", "auto"]}),
                 ("Neural Network", MLPRegressor(), {"hidden_layer_sizes": [(50,), (100,)], "activation": ["relu", "tanh"], "max_iter": [2000]})]

formulas = [("Height Formula", X_test[:,2] / 10 + 5),
            ("Age Formula", np.select([X_test[:,1] < 0.5, X_test[:,1] < 1, X_test[:,1] < 2], [9, 10, 11], default=12 + X_test[:,1] * 0.5)),
            ("Tube ID Formula", 3 * df.iloc[X_test[:,0].astype(int), df.columns.get_loc("tube")])]

df1 = pd.DataFrame()
for (model_name, model, params) in models_params:
    grid_search = GridSearchCV(model, params, cv=5)
    grid_search.fit(X_train, y_train)
    y_pred_ml = grid_search.predict(X_test)
    residuals_ml = (y_test - y_pred_ml) ** 2

    for formula_name, y_pred_formula in formulas:
        residuals_formula = (y_test - y_pred_formula) ** 2
        t_result = ttest_rel(residuals_ml, residuals_formula)
        df1.loc[f"Comparison of {model_name} and {formula_name}", "p-value"] = t_result.pvalue

df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = { 'Total number of observations': len(df) }
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

