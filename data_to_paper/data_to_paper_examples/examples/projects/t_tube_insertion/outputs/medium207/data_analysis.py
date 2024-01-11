
# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed

# PREPROCESSING
# Assigning descriptive labels to the 'sex' column
df['patient_sex'] = df['sex'].map({0: 'female', 1: 'male'})

# Creating dummy variables
preprocessed_df = pd.get_dummies(df, columns=['patient_sex'])

# ANALYSIS

## Table 1: Comparison of MSE of Two Models - Random Forest and Formula-Based Model

# Dividing into train and test datasets
X = preprocessed_df[['patient_sex_male', 'age_c', 'ht', 'wt']]
y = preprocessed_df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Building and training the random forest model
forest_reg = RandomForestRegressor()
param_grid = [{'n_estimators': [3, 10, 30], 'max_features': [2, 4, 6]}]
grid_search = GridSearchCV(forest_reg, param_grid, cv=5, scoring='neg_mean_squared_error', return_train_score=True)
grid_search.fit(X_train, y_train)

# Assigning the best model from the grid search
model = grid_search.best_estimator_
pred_rf = model.predict(X_test)

# Building and predicting with the formula-based model
pred_f = X_test['ht'] / 10 + 5

# Comparing the mean squared error of the two models
rf_mse = mean_squared_error(y_test, pred_rf)
formula_mse = mean_squared_error(y_test, pred_f)

# Performing a paired t-test between the predictions of the two models
ttest_result = ttest_rel(pred_rf, pred_f)

# Creating a dataframe to store MSEs and p-value
df1 = pd.DataFrame({
    'Model': ['Random Forest', 'Formula-Based'],
    'MSE': [rf_mse, formula_mse]
})
df1.loc['T-test p-value'] = [ttest_result.pvalue, '']
df1.to_pickle('table_1.pkl')

## Table 2: Model Parameters and Hyperparameters
df2 = pd.DataFrame(grid_search.best_params_, index=['Best Parameters'])
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),
    'accuracy of regression model': model.score(X_test, y_test)
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
