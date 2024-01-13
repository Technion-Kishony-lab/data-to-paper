
# IMPORT
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
import pickle
from scipy import stats

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of the dataset"
desc_stats = df.describe().loc[['mean', 'std']]   # include only mean and standard deviation
desc_stats.to_pickle('table_0.pkl')

# PREPROCESSING 
features = ['sex', 'age_c', 'ht', 'wt']
target = 'tube_depth_G'

# dividing data into training and testing sets
x_train, x_test, y_train, y_test = train_test_split(df[features], df[target], test_size=0.3, random_state=42)

# ANALYSIS
## Table 1: "Performance metrics for different models"
results = {}
models = [RandomForestRegressor(), ElasticNet(), SVR(), MLPRegressor(max_iter=1000, random_state=42)]
names = ["Random Forest", "Elastic Net", "Support Vector Machine", "Neural Network"]

for i, model in enumerate(models):
    model.fit(x_train, y_train) # fit the model
    y_pred = model.predict(x_test) # make prediction on the test split
    mse = mean_squared_error(y_test, y_pred) # calculate mean squared error
    results[names[i]] = mse

df1 = pd.DataFrame.from_dict(results, orient='index', columns=['Mean Squared Error']).sort_values(by='Mean Squared Error')
df1 = df1.iloc[:3,:]  # Choose top 3 models
df1.to_pickle('table_1.pkl')

## Table 2: "Performance metrics for formula-based models"
results_formula = {}

# height-based model
OTTD_ht = df['ht'] / 10 + 5
mse_ht = mean_squared_error(df['tube_depth_G'], OTTD_ht)
results_formula['Height Model'] = mse_ht

# age-based model
age = df['age_c']
OTTD_age = np.where(age < 0.5, 9, np.where(age < 1, 10, np.where(age < 2, 11, 12 + age * 0.5)))
mse_age = mean_squared_error(df['tube_depth_G'], OTTD_age)
results_formula['Age Model'] = mse_age

# id-based model
OTTD_id = 3 * df['tube']
mse_id = mean_squared_error(df['tube_depth_G'], OTTD_id)
results_formula['ID Model'] = mse_id

df2 = pd.DataFrame.from_dict(results_formula, orient='index', columns=['Mean Squared Error'])
df2.to_pickle('table_2.pkl')

# t-test comparison
ml_mse = df1['Mean Squared Error'].values
formula_mse = df2['Mean Squared Error'].values

ttest_res = stats.ttest_rel(ml_mse, formula_mse)

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0],
 't-statistic of paired t-test between ML and formula-based models' : ttest_res.statistic,
 'p-value of paired t-test between ML and formula-based models' : ttest_res.pvalue
}

with open('additional_results.pkl', 'wb') as f:
   pickle.dump(additional_results, f)
