
# IMPORT
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error
from scipy import stats

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed for this analysis.

# PREPROCESSING 
# No preprocessing is needed, because data is already preprocessed and ready for analysis.

# ANALYSIS

# Table 1: "Performance summary of Random Forest and Elastic Net models"
features = data[["sex", "age_c", "ht", "wt"]]
target = data["tube_depth_G"]
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

rf = RandomForestRegressor(random_state=42)
params_rf = {'n_estimators': [50, 100, 200], 'max_depth': [None, 10, 30], 'min_samples_split': [2, 5, 10]}
grid_rf = GridSearchCV(estimator=rf, param_grid=params_rf, cv=3)
grid_rf.fit(X_train, y_train)
rf_pred = grid_rf.predict(X_test)
rf_sq_resid = (rf_pred - y_test) ** 2

en = ElasticNet(random_state=42)
params_en = {'alpha': [0.1, 0.5, 1], 'l1_ratio': [0.2, 0.5, 0.8]}
grid_en = GridSearchCV(estimator=en, param_grid=params_en, cv=3)
grid_en.fit(X_train, y_train)
en_pred = grid_en.predict(X_test)
en_sq_resid = (en_pred - y_test) ** 2

model_performace = pd.DataFrame({
    "Model": ["Random Forest", "Elastic Net"],
    "RMSE": [np.sqrt(mean_squared_error(y_test, rf_pred)), np.sqrt(mean_squared_error(y_test, en_pred))],
    "Best Params": [str(grid_rf.best_params_), str(grid_en.best_params_)]
})
model_performace.set_index('Model', inplace=True)
model_performace.to_pickle('table_1.pkl')

# Table 2: "Paired t-test results for squared residuals of Random Forest and Elastic Net models"
t_test_results = stats.ttest_rel(rf_sq_resid, en_sq_resid)
t_test_df = pd.DataFrame({
    "Statistic": ["T-statistic", "p-value"],
    "Value": [t_test_results.statistic, t_test_results.pvalue]
})
t_test_df.set_index('Statistic', inplace=True)
t_test_df.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': data.shape[0], 
    'Ideal tube_depth_G range': [data.tube_depth_G.min(), data.tube_depth_G.max()],
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
