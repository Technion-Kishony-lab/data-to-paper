
# IMPORT
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split, GridSearchCV
from scipy.stats import ttest_rel
import pickle

# LOAD DATA
data = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed as the initial data is well-prepared.

# DESCRIPTIVE STATISTICS
# Table 0: Descriptive statistics of height and age stratified by sex
df0 = data.groupby("sex")[["ht", "age_c"]].mean()
df0.index = df0.index.map({0: 'female', 1: 'male'})
df0 = df0.rename(columns={'ht': 'Avg. Height (cm)', 'age_c': 'Avg. Age (years)'}) # Rename columns for clarity
df0.to_pickle('table_0.pkl')

# PREPROCESSING
# No preprocessing is necessary because there are no categorical variables or missing data.

# ANALYSIS

#Splitting the data into training set and test set
X = data[['sex','age_c','ht','wt']]
y = data['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Preparing for Hyperparameter Tuning
rf = RandomForestRegressor()
params_rf = {'n_estimators': [50, 100, 200],'max_depth': [10, 20, 30],'min_samples_split': [2, 5, 10]}
grid_rf = GridSearchCV(estimator=rf, param_grid=params_rf, cv=5)

#Train the Model
grid_rf.fit(X_train,y_train)

#Predicting on the Test set
rf_pred = grid_rf.predict(X_test)

# Squared residuals for the Random forest
rf_residuals = (rf_pred - y_test) ** 2

#Elastic Net
en = ElasticNet()
params_en = {'alpha': [0.1, 0.5, 1.0],'l1_ratio': [0.1, 0.5, 1.0]}
grid_en = GridSearchCV(estimator=en, param_grid=params_en, cv=5)

#Train the Model
grid_en.fit(X_train,y_train)

#Predicting on the Test set
en_pred = grid_en.predict(X_test)

# Squared residuals for the Elastic Net model
en_residuals = (en_pred - y_test) ** 2

#Statistical test: Paired t-test to compare RF and EN squared residuals
t_test_result = ttest_rel(rf_residuals, en_residuals)

#Table 1: Comparison of predictive performance of two models
df1 = pd.DataFrame({"Model": ["RF", "EN"],
                    "Mean Squared Residuals": [rf_residuals.mean(), en_residuals.mean()],
                    "STD of Squared Residuals": [rf_residuals.std(), en_residuals.std()],
                    "p-value": [t_test_result.pvalue, t_test_result.pvalue]}
                  )

df1.set_index("Model", inplace=True)

df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(data), 
 'Best parameters for RF': grid_rf.best_params_,
 'Best parameters for EN': grid_en.best_params_,
}
with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
