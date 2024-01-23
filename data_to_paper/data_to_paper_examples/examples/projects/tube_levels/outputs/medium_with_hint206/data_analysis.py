
# IMPORT
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel, sem
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GridSearchCV
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed, because our data is already in a format suitable for analysis.

# ANALYSIS
# Table 1: "Comparison of Mean Squared Residuals, with associated Standard Errors, between Machine Learning Model and Formula-based Model."

# Split the data into training and testing sets
X = df[['sex','age_c','ht','wt']]
y = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Hyperparameter tuning for Random Forest Regressor using GridSearchCV
parameters = {'n_estimators':[50, 100, 150, 200], 'max_depth':[None, 5, 10, 15, 20]}
rf = RandomForestRegressor(random_state=42)
clf = GridSearchCV(rf, parameters)
clf.fit(X_train, y_train)
best_params = clf.best_params_

# Train the model using the best parameters
rf = RandomForestRegressor(n_estimators=best_params['n_estimators'], max_depth=best_params['max_depth'], random_state=42)
rf.fit(X_train, y_train)

# Predict OTTD using the trained model and calculate squared residuals
y_pred_rf = rf.predict(X_test)
squared_residuals_rf = (y_test - y_pred_rf)**2

# Calculate OTTD using formula-based model and calculate squared residuals
y_pred_formula = X_test['ht'] / 10 + 5
squared_residuals_formula = (y_test - y_pred_formula)**2

# Perform paired t-test on squared residuals and preserve the results as an object for further attribute access
t_test_results = ttest_rel(squared_residuals_rf, squared_residuals_formula)

# Calculate standard errors
se_rf = sem(squared_residuals_rf)
se_formula = sem(squared_residuals_formula)

# Prepare the dataframe for Table 1
df1 = pd.DataFrame({'Method': ['Random Forest', 'Formula-based'],
                    'Mean Squared Residual': [squared_residuals_rf.mean(), squared_residuals_formula.mean()],
                    'Standard Error': [se_rf, se_formula]
                    })
df1.set_index('Method', inplace=True)

# Save the dataframe
df1.to_pickle('table_1.pkl')

# Table 2: "Feature importances from the Random Forest model."

# Extract feature importances and prepare the dataframe for Table 2
feature_importances = rf.feature_importances_
df2 = pd.DataFrame({'Feature': X.columns,
                    'Importance': feature_importances
                   })
df2.set_index('Feature', inplace=True)

# Save the dataframe
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
# Save the best parameters of RF model and p-value of the t-test to additional_results.pkl 
additional_results = {
 'Best Parameters of RF Model': best_params,
 'P-value of T-test': t_test_results.pvalue
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
