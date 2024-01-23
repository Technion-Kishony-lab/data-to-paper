

# IMPORT
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import f_oneway, friedmanchisquare
import warnings
import pickle
warnings.filterwarnings('ignore')

# LOAD DATA
df = pd.read_csv("tracheal_tube_insertion.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING 
# No preprocessing is needed, because all variables are already numerical and there are no missing values.

# ANALYSIS
# Features and target
X = df[['sex', 'age_c', 'ht', 'wt']]
y = df['tube_depth_G']

# Machine Learning Models & Test Train Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

# Set the models
models = {
    "Random Forest": GridSearchCV(RandomForestRegressor(random_state=0), param_grid={"n_estimators": [10, 100, 1000], "max_depth": [None, 10, 20, 30]}),
    "ElasticNet": GridSearchCV(ElasticNet(random_state=0), param_grid={"alpha": [0.1, 0.5, 1], "l1_ratio": [0.1, 0.5, 1]}),
    "SVR": GridSearchCV(SVR(), param_grid={"C": [0.1, 0.5,1]}),
    "MLP": GridSearchCV(MLPRegressor(max_iter=2000, random_state=0), param_grid={"hidden_layer_sizes": [(50,), (20,20)], "alpha": [0.0001, 0.001, 0.01]})
}

mse = {}
residuals = {}

for model_name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse[model_name] = mean_squared_error(y_test, y_pred)
    residuals[model_name] = (y_test - y_pred)**2

# Formula-Based Models
height_model = X_test['ht']/10 + 5
age_model = pd.Series(9, index=X_test.index)
age_model.loc[(0.5 <= X_test['age_c']) & (X_test['age_c'] < 1)] = 10
age_model.loc[(1 <= X_test['age_c']) & (X_test['age_c'] < 2)] = 11
age_model.loc[(2 <= X_test['age_c'])] = 12 + 0.5*X_test['age_c']
tube_id_model = X_test['ht']/10 + 5

for name, model in zip(["Height Model", "Age Model", "Tube ID Model"], [height_model, age_model, tube_id_model]):
    mse[name] = mean_squared_error(y_test, model)
    residuals[name] = (y_test - model)**2

# Table 1: Comparison of squared residuals of ML and formula-based models
df1 = pd.DataFrame(mse, index=["MSE"]).T
df1.index.name = "Model"
df1.to_pickle("table_1.pkl")

# SAVE ADDITIONAL RESULTS
results = f_oneway(*residuals.values())
additional_results = {'ANOVA': {'F-value': results.statistic,
                               'p-value': results.pvalue }}

# If ANOVA is significant, perform pairwise Bonferroni-corrected T-tests
residuals_arr = np.array(list(residuals.values()))
friedman = friedmanchisquare(*residuals_arr)
additional_results['Friedman'] = {'statistic': friedman.statistic,
                                  'p-value': friedman.pvalue}

with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
