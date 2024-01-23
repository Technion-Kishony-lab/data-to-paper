
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from scipy import stats
import pickle

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# No preprocessing is needed.

# ANALYSIS
## Table 1: "Comparison of prediction performance using Machine Learning model and formula-based model"

# Split into train/test set
train, test = train_test_split(data, test_size=0.2, random_state=1)

# Train random forest model with GridSearchCV
rf = RandomForestRegressor(random_state=1)
param_grid = {
    'n_estimators': [10, 50, 100],
    'max_depth': [None, 2, 5, 10]
}
gs = GridSearchCV(rf, param_grid, cv=5)
gs.fit(train[["sex", "age_c", "ht", "wt"]], train["tube_depth_G"])
best_rf = gs.best_estimator_

# Predict for test set
test["rf_prediction"] = best_rf.predict(test[["sex", "age_c", "ht", "wt"]])

# Compute predictions using formula-based model
test["formula_prediction"] = test["ht"] / 10 + 5

# Compute residuals
test["rf_residual"] = (test["tube_depth_G"] - test["rf_prediction"])**2
test["formula_residual"] = (test["tube_depth_G"] - test["formula_prediction"])**2

# Create dataframe for scientific table 1 summarizing residuals
df1 = pd.DataFrame({
    "Model": ["Random Forest", "Height Formula"],
    "Mean squared residual": [np.mean(test["rf_residual"]), np.mean(test["formula_residual"])],
    "Standard deviation of residual": [np.std(test["rf_residual"]), np.std(test["formula_residual"])]
}, index=["RF", "Formula"])

df1.to_pickle('table_1.pkl')

## Table 2: "Summary statistics for actual and predicted OTTD for both models"

# Compute summary statistics for each set of predictions
df2 = pd.DataFrame({
    "Statistic": ["Mean", "Standard deviation"],
    "Actual OTTD": [test["tube_depth_G"].mean(), test["tube_depth_G"].std()],
    "Predicted OTTD (Random Forest)": [test["rf_prediction"].mean(), test["rf_prediction"].std()],
    "Predicted OTTD (Height Formula)": [test["formula_prediction"].mean(), test["formula_prediction"].std()]
}, index=["Mean", "Standard Deviation"])

df2.to_pickle('table_2.pkl')

# Conduct paired t-test
ttest_results = stats.ttest_rel(test["rf_residual"], test["formula_residual"])
assert ttest_results.pvalue < 0.05, f"Paired t-test failed with p-value: {ttest_results.pvalue}"

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data), 
 'Random Forest Model R-squared': best_rf.score(test[["sex", "age_c", "ht", "wt"]], test["tube_depth_G"]),
 'Paired t-test p-value': ttest_results.pvalue,
 'Best Random Forest hyperparameters': gs.best_params_,
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
