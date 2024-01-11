
# IMPORT
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed in this case.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed in this case.

# PREPROCESSING
# Splitting the dataset into the predictors and target variable
x = df[['sex', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']

# Defining the train and test sets
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

# ANALYSIS
# Table 1: "Comparison of predictive performance between Random Forest and Elastic Net Models"
# Random Forest Model
rf = RandomForestRegressor()
parameters = {'n_estimators': range(20, 100, 10), 'max_depth': range(2, 8, 2)}
rf_optimal = GridSearchCV(rf, parameters, cv=5)
rf_optimal.fit(x_train, y_train)

# Apply the model to the test data
predictions_rf = rf_optimal.predict(x_test)
residuals_rf = (y_test - predictions_rf) ** 2

# Elastic Net Model
en = ElasticNet()
parameters = {'alpha': [0.0001, 0.001, 0.01, 0.1, 1, 10], 'l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9]}
en_optimal = GridSearchCV(en, parameters, cv=5)
en_optimal.fit(x_train, y_train)

# Apply the model to the test data
predictions_en = en_optimal.predict(x_test)
residuals_en = (y_test - predictions_en) ** 2

# Perform a paired t-test
ttest_results = ttest_rel(residuals_rf, residuals_en)

# Record results in a DataFrame
df1 = pd.DataFrame({
    'Model': ['Random Forest', 'Elastic Net'],
    'Mean Squared Residual': [residuals_rf.mean(), residuals_en.mean()],
    't_statistic': [ttest_results.statistic, ttest_results.statistic],
    'p_value': [ttest_results.pvalue, ttest_results.pvalue]
}, index=['Model 1: RF', 'Model 2: EN'])

df1.to_pickle('table_1.pkl')


# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df), 
 'accuracy of Random Forest model': rf_optimal.best_score_,
 'accuracy of Elastic Net model': en_optimal.best_score_
}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

