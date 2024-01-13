
# IMPORT
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
import warnings
from sklearn.exceptions import ConvergenceWarning
import pickle

# Ignore convergence warning from Neural Network model
warnings.filterwarnings('ignore', category=ConvergenceWarning)

# LOAD DATA
df = pd.read_csv('tracheal_tube_insertion.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# Convert the categorical variable to dummies
df = pd.get_dummies(df, columns=['sex'], drop_first=True)

# ANALYSIS
## Table 1: "Paired t-tests between ML models and formula-based models"

# Splitting the data into train and test sets
X = df[df.columns.difference(['tube_depth_G'])]
y = df['tube_depth_G']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=123)

# ML Models
models = {
    "Random Forest": RandomForestRegressor(),
    "Elastic Net": ElasticNet(),
    "Support Vector Machine": SVR(),
    "Neural Network": MLPRegressor(max_iter=500) # Increase max_iter to prevent convergence warning
}

# Formula-based Models
formulas = {
    "Height Formula": lambda x: x / 10 + 5,
    "Age Formula": lambda x: 9 if x < 0.5 else 10 if x < 1 else 11 if x < 2 else 12 + x*0.5,
    "ID Formula": lambda x: 3 * x
}

# Dataframe for storing results
df1 = pd.DataFrame(index=list(models.keys()), columns=list(formulas.keys()))

# Fitting ML models and performing paired t-tests with formula-based models
for modelName, model in models.items():
    model.fit(X_train, y_train)
    ml_predictions = model.predict(X_test)
    residuals_ml = np.square(y_test - ml_predictions)
    
    for formulaName, formula in formulas.items():
        formula_predictions = X_test.apply(lambda row: formula(row['ht' if formulaName=="Height Formula" else 'age_c' if formulaName=="Age Formula" else 'tube']), axis=1)
        residuals_formula = np.square(y_test - formula_predictions)
        ttest_results = ttest_rel(residuals_ml, residuals_formula)
        df1.loc[modelName, formulaName] = ttest_results.pvalue
        
df1.to_pickle('table_1.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': df.shape[0]
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
