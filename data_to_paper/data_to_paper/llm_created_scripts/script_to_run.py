
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import make_regression

X, y = make_regression(n_samples=100, n_features=3, noise=0.1, random_state=42)
param_grid = {
    'n_estimators': [30, 60, 90],
    'max_depth': [2, 4, 6],
    'min_samples_split': [2, 4, 6]
}
rf = RandomForestRegressor()
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5)
grid_search.fit(X, y)
print(grid_search.best_params_)
