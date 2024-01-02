import pytest
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.datasets import load_iris
from data_to_paper.run_gpt_code.overrides.sklearn.override_sklearn import SklearnSearchLimitCheck
from data_to_paper.run_gpt_code.types import RunIssue


def test_grid_search_cv_limit_check():
    with SklearnSearchLimitCheck(max_iterations=5):
        # Example data
        iris = load_iris()
        param_grid = {'max_depth': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
        grid_search = GridSearchCV(DecisionTreeClassifier(), param_grid, cv=3)

        with pytest.raises(RunIssue) as excinfo:
            grid_search.fit(iris.data, iris.target)
        assert "exceeds the maximum allowed iterations" in str(excinfo.value)


def test_randomized_search_cv_limit_check():
    with SklearnSearchLimitCheck(max_iterations=5):
        # Example data
        iris = load_iris()
        param_distributions = {'max_depth': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
        randomized_search = RandomizedSearchCV(DecisionTreeClassifier(), param_distributions, n_iter=20, cv=3)

        with pytest.raises(RunIssue) as excinfo:
            randomized_search.fit(iris.data, iris.target)
        assert "exceeds the maximum allowed iterations" in str(excinfo.value)


def test_grid_search_cv_within_limit():
    with SklearnSearchLimitCheck(max_iterations=5):
        # Example data
        iris = load_iris()
        param_grid = {'max_depth': [1, 2, 3]}  # Limited to 3 options
        grid_search = GridSearchCV(DecisionTreeClassifier(), param_grid, cv=3)

        # Should complete without errors
        grid_search.fit(iris.data, iris.target)
        assert len(grid_search.cv_results_['mean_test_score']) <= 3


def test_randomized_search_cv_within_limit():
    with SklearnSearchLimitCheck(max_iterations=5):
        # Example data
        iris = load_iris()
        param_distributions = {'max_depth': [1, 2, 3, 4, 5]}  # 5 options, but within limit due to n_iter
        randomized_search = RandomizedSearchCV(DecisionTreeClassifier(), param_distributions, n_iter=3, cv=3)

        # Should complete without errors
        randomized_search.fit(iris.data, iris.target)
        assert len(randomized_search.cv_results_['mean_test_score']) <= 3
