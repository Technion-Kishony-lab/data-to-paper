
# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from scipy import stats
import pickle

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# No preprocessing is needed because all features are numerical 

# ANALYSIS
# Table 1: "Performance comparison of Random Forest Model (RFM) and Height Formula-Based Model (HFMB)"
features = df.drop(columns=['tube_depth_G', 'tube'])
target = df['tube_depth_G']

# Split into train and test set
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size = 0.2, random_state = 42)

# Random Forest Model with GridSearchCV for hyperparameter tuning
parameters = {'n_estimators':[50,100,200], 'max_depth':[3,5,7, None]}
rf = RandomForestRegressor(random_state = 42)
clf = GridSearchCV(rf, parameters, cv=5)
clf.fit(X_train, y_train)
rf_predictions = clf.predict(X_test)

# Height Formula-Based Model
heights = X_test['ht']
hfmb_predictions = heights/10 + 5

# Compute Residuals square
rf_residuals_sq = (rf_predictions - y_test)**2
hfmb_residuals_sq = (hfmb_predictions - y_test)**2

# Perform paired t-test
ttest_results = stats.ttest_rel(rf_residuals_sq, hfmb_residuals_sq)

df1 = pd.DataFrame({
    'Model': ['RFM', 'HFMB'],
    'Mean_Squared_Residuals': [rf_residuals_sq.mean(), hfmb_residuals_sq.mean()],
    't_statistic': [ttest_results.statistic, ttest_results.statistic],
    'p_value': [ttest_results.pvalue, ttest_results.pvalue]
})

df1.set_index('Model', inplace=True)
df1.to_pickle('table_1.pkl')

# Table 2: "Feature Importance of Random Forest Model"
importances = pd.DataFrame({
    'Feature': X_train.columns,
    'Importance': clf.best_estimator_.feature_importances_
})
importances.set_index('Feature', inplace=True)
importances.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),
    'RFM_best_params': clf.best_params_,
    'RFM_training_score': clf.score(X_train, y_train),
    'RFM_test_score': clf.score(X_test, y_test)
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
    
