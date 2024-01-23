
# IMPORT
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error
from scipy import stats
import numpy as np
import pickle
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
df_male = df[df['sex'] == 1]
df_female = df[df['sex'] == 0]
df0 = pd.concat([df_male.describe()[['age_c', 'ht']], df_female.describe()[['age_c', 'ht']]], keys=['Male', 'Female'])
df0.to_pickle('table_0.pkl')

# PREPROCESSING
scaler = StandardScaler()
df[['age_c_std', 'ht_std', 'wt_std']] = scaler.fit_transform(df[['age_c', 'ht', 'wt']])    

# ANALYSIS
features = ['sex', 'age_c_std', 'ht_std', 'wt_std']
target = 'tube_depth_G'

X_train, X_test, y_train, y_test = train_test_split(df[features], df[target], test_size=0.2, random_state=42)

## Table 1: "Hyper-parameter tuning and model performance evaluation for Random Forest and Elastic Net"
params_rf = {'n_estimators': [10, 50, 100, 200], 'max_depth': [5, 10, 15, 20]}
grid_rf = GridSearchCV(RandomForestRegressor(), params_rf, cv=5)
grid_rf.fit(X_train, y_train)

params_en = {'alpha': [0.1, 0.5, 1, 5], 'l1_ratio': [0, 0.3, 0.5, 0.7, 1]}
grid_en = GridSearchCV(ElasticNet(max_iter=1000000, tol=0.001), params_en, cv=5)
grid_en.fit(X_train, y_train)

rf_predicted = grid_rf.predict(X_test)
en_predicted = grid_en.predict(X_test)

rf_residuals = y_test - rf_predicted
en_residuals = y_test - en_predicted

paired_ttest_results = stats.ttest_rel(np.square(rf_residuals), np.square(en_residuals))

df1 = pd.DataFrame({'Model': ['Random Forest', 'Elastic Net'],
                    'Best Parameters': [str(grid_rf.best_params_), str(grid_en.best_params_)],
                    'Residual Mean': [np.mean(rf_residuals), np.mean(en_residuals)],
                    'Residual STD': [np.std(rf_residuals), np.std(en_residuals)],
                    'T-stat': [paired_ttest_results.statistic, paired_ttest_results.statistic],
                    'P-value': [paired_ttest_results.pvalue, paired_ttest_results.pvalue]})
df1.set_index('Model', inplace=True)
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Residuals RF': rf_residuals.tolist(),
    'Residuals EN': en_residuals.tolist(),
    'Total number of observations': len(df),
    'Hyperparameters RF': str(grid_rf.best_params_),
    'Hyperparameters EN': str(grid_en.best_params_)
}
with open("additional_results.pkl", "wb") as f:
    pickle.dump(additional_results, f)
