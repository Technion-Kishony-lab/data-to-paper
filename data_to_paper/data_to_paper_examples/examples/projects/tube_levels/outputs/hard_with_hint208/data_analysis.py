

# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from scipy import stats
import pickle


# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')


# DATASET PREPARATIONS
# No dataset preparations were needed.


# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.


# PREPROCESSING
scaler = StandardScaler()
df.loc[:, ['age_c', 'ht', 'wt']] = scaler.fit_transform(df.loc[:, ['age_c', 'ht', 'wt']])


# ANALYSIS
y = df['tube_depth_G']
X = df.drop(['tube', 'tube_depth_G'], axis=1)

# Machine Learning Models
models = {"RF": RandomForestRegressor(),
          "EN": ElasticNet(),
          "SVM": SVR(),
          "NN": MLPRegressor(max_iter=1000)}

params = {"RF": {'n_estimators': [100, 200, 300], 'max_depth': [5, 10, 15]},
          "EN": {'alpha': [0.1, 1], 'l1_ratio': [0.5, 0.8]},
          "SVM": {'C': [0.1, 1, 10], 'epsilon': [0.1, 0.2, 0.3]},
          "NN": {'hidden_layer_sizes': [(50,), (30, 20)], 'alpha': [0.0001, 0.001]}}

ml_results = {}
for model in models.keys():
    grid = GridSearchCV(models[model], params[model], cv=3)
    grid.fit(X, y)
    preds = grid.predict(X)
    residuals = np.square(preds - y)
    ml_results[model] = residuals
    
# Formula-based models
height_preds = df['ht'] / 10 + 5
age_preds = np.select(
    [df['age_c'] < 0.5, df['age_c'] < 1, df['age_c'] < 2],
    [9, 10, 11],
    default= 12 + df['age_c'] * 0.5
)
id_preds = 3 * df['tube']

formulas_results = {
    "Height": np.square(height_preds - y),
    "Age": np.square(age_preds - y),
    "ID": np.square(id_preds - y)
}

# Statistical test
stat_test_results = []
for name_ml, residuals_ml in ml_results.items():
    for name_formula, residuals_formula in formulas_results.items():
        t_test_results = stats.ttest_ind(residuals_ml, residuals_formula)
        stat_test_results.append({"ML_Model": name_ml,
                                  "Formula_Model": name_formula,
                                  "T_Statistic": t_test_results.statistic,
                                  "P_Value": t_test_results.pvalue})

df_statistics = pd.DataFrame(stat_test_results)
df_statistics = df_statistics.set_index(['ML_Model', 'Formula_Model'])
df_statistics.to_pickle("table_0.pkl")


# SAVE ADDITIONAL RESULTS
additional_results = {'Total number of observations': df.shape[0]}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

