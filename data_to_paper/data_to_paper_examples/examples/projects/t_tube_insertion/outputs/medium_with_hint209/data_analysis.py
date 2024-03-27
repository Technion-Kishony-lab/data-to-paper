
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics are needed.

# PREPROCESSING
# Creating dummies for the categorical variable: sex
df = pd.get_dummies(df, columns=['sex'], drop_first=True)

# ANALYSIS
## Table 1: Comparison of Mean Squared Residuals between ML model and Formula-based model

# Splitting the data into train and test set
X_train, X_test, y_train, y_test = train_test_split(df[['tube','sex_1','age_c','ht','wt']], df['tube_depth_G'], test_size=0.2, random_state=42)

# Defining parameters grid for Random Forest
param_grid = {
    'max_depth': [5, 10, 15, 20, 25, 30],
    'n_estimators': [50, 100, 200, 300, 500]
}

# Random Forest with random search for hyperparameters optimization
rf = RandomForestRegressor()
rf_random = RandomizedSearchCV(estimator=rf, param_distributions=param_grid, cv=3, random_state=42)
rf_random.fit(X_train, y_train)

# Predictions
y_pred_rf = rf_random.predict(X_test)
# Placeholder for formula calculation. An example formula could be "(height + age)/4".
y_pred_formula = (X_test['ht'] + X_test['age_c']) / 4  

# Calculating squared residuals
rf_residuals = (y_test - y_pred_rf)**2
formula_residuals = (y_test - y_pred_formula)**2

# Confidence Intervals Calculation
confidence_level = 0.95
sample_mean_rf = rf_residuals.mean()
sample_std_rf = rf_residuals.std()
sample_size_rf = len(rf_residuals)
confidence_interval_rf = stats.t.interval(confidence_level, sample_size_rf-1, loc=sample_mean_rf, scale=sample_std_rf/np.sqrt(sample_size_rf))

sample_mean_formula = formula_residuals.mean()
sample_std_formula = formula_residuals.std()
sample_size_formula = len(formula_residuals)
confidence_interval_formula = stats.t.interval(confidence_level, sample_size_formula-1, loc=sample_mean_formula, scale=sample_std_formula/np.sqrt(sample_size_formula))

# Creating the dataframe for the table
df1 = pd.DataFrame({
    'Model': ['RF model', 'Formula-based model'],
    'Mean_Squared_Residuals': [sample_mean_rf, sample_mean_formula],
    'Confidence_Interval_For_Mean_Squared_Residuals': [confidence_interval_rf, confidence_interval_formula]
})
df1.set_index('Model', inplace=True)

# Saving the data frame to pickle file
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),
    'Best parameters for RF model': rf_random.best_params_,
    'Accuracy of optimized RF model': np.sqrt(mean_squared_error(y_test, y_pred_rf)),
    'P-value for paired t-test comparing mean squared residuals': stats.ttest_rel(rf_residuals, formula_residuals).pvalue
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
