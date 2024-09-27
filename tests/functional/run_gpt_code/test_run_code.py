import os
import time
from types import ModuleType

import pytest

from data_to_paper.research_types.hypothesis_testing.coding.analysis.coding import \
    DictPickleContentOutputFileRequirement
from data_to_paper.run_gpt_code.code_runner import CodeRunner, FailedRunningCode
from data_to_paper.run_gpt_code.exceptions import CodeUsesForbiddenFunctions, \
    CodeWriteForbiddenFile, CodeImportForbiddenModule, UnAllowedFilesCreated
from data_to_paper.run_gpt_code.overrides.contexts import OverrideStatisticsPackages
from data_to_paper.run_gpt_code.overrides.sklearn.override_sklearn import SklearnRandomStateOverride, \
    SklearnNNSizeOverride
from data_to_paper.run_gpt_code.overrides.random import SetRandomSeeds
from data_to_paper.run_gpt_code.run_issues import RunIssue
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirements
from data_to_paper.text import dedent_triple_quote_str


class CallFuncCodeRunner(CodeRunner):
    def _run_function_in_module(self, module: ModuleType):
        return module.func()


def test_run_code_on_legit_code():
    code = dedent_triple_quote_str("""
        def f():
            return 'hello'
        """)
    run_code = CodeRunner()
    run_code.run(code)
    assert run_code._module.f() == 'hello'


def test_run_code_correctly_reports_exception():
    code = dedent_triple_quote_str("""
        # line 1
        # line 2
        raise Exception('error')
        # line 4
        """)
    error = CodeRunner().run(code)[3]
    assert isinstance(error, FailedRunningCode)
    assert error.exception.msg == 'error'
    linenos_lines, msg = error.get_lineno_line_message()
    assert linenos_lines == [(3, "raise Exception('error')")]


def test_import_statsmodels():
    # this caused a bug on Windows.
    # the import is using try-except on imports to check ig packages exists
    code = "import statsmodels.api as sm"
    error = CodeRunner().run(code)[3]
    assert error is None


def test_run_code_raises_warning():
    code = dedent_triple_quote_str("""
        import warnings
        warnings.warn('be careful', UserWarning)
        """)
    error = CodeRunner(warnings_to_raise=[UserWarning]).run(code)[3]
    assert isinstance(error, FailedRunningCode)
    lineno_line, msg = error.get_lineno_line_message()
    assert msg == 'be careful'
    assert lineno_line == [(2, "warnings.warn('be careful', UserWarning)")]


def test_run_code_issues_warning():
    code = dedent_triple_quote_str("""
        import warnings
        warnings.warn('be careful', UserWarning)
        """)
    result, created_files, multi_context, e = CodeRunner(warnings_to_issue=[UserWarning]).run(code)
    issues = multi_context.issues
    assert e is None
    assert len(issues) == 1
    assert 'be careful' in issues[0].issue
    assert issues[0].linenos_and_lines == [(2, "warnings.warn('be careful', UserWarning)")]


def test_run_code_correctly_reports_exception_from_func():
    code = dedent_triple_quote_str("""
        def func():
            raise Exception('stupid error')
        func()
        """)
    error = CodeRunner().run(code)[3]
    assert isinstance(error, FailedRunningCode)
    assert 'stupid error' in str(error.exception)
    linenos_lines, msg = error.get_lineno_line_message()
    assert linenos_lines == [(3, 'func()'), (2, "raise Exception('stupid error')")]
    msg = error.get_traceback_message()
    assert 'func()' in msg
    assert "raise Exception('stupid error')" in msg
    assert 'stupid error' in msg


@pytest.mark.parametrize("forbidden_call", ['input', 'exit', 'quit', 'eval'])
def test_run_code_forbidden_functions(forbidden_call):
    time.sleep(0.1)
    code = dedent_triple_quote_str("""
        a = 1
        {}()
        """).format(forbidden_call)
    error = CodeRunner().run(code)[3]
    assert isinstance(error, FailedRunningCode)
    assert isinstance(error.exception, CodeUsesForbiddenFunctions)
    lineno_lines, msg = error.get_lineno_line_message()
    assert lineno_lines == [(2, '{}()'.format(forbidden_call))]
    # TODO: some wierd bug - the message is not always the same:
    # assert forbidden_call in msg


def test_run_code_forbidden_function_print():
    code = dedent_triple_quote_str("""
        a = 1
        print(a)
        a = 2
        """)
    result, created_files, multi_context, error = CodeRunner().run(code)
    assert 'print' in multi_context.issues[0].issue


@pytest.mark.parametrize("forbidden_import,module_name", [
    ('import os', 'os'),
    ('from os import path', 'os'),
    ('import os.path', 'os.path'),
    ('import sys', 'sys'),
    ('import matplotlib', 'matplotlib'),
    ('import matplotlib as mpl', 'matplotlib'),
    ('import matplotlib.pyplot as plt', 'matplotlib.pyplot'),
])
def test_run_code_forbidden_import(forbidden_import, module_name):
    code = dedent_triple_quote_str("""
        import scipy
        import numpy as np
        {}
        """).format(forbidden_import)
    if 'matplotlib' in module_name:
        run_code = CodeRunner(modified_imports=(('matplotlib', None),))
    else:
        run_code = CodeRunner()
    error = run_code.run(code)[3]
    assert isinstance(error, FailedRunningCode)
    assert isinstance(error.exception, CodeImportForbiddenModule)
    assert error.exception.module == module_name
    lineno_lines, msg = error.get_lineno_line_message()
    assert lineno_lines == [(3, forbidden_import)]


def test_run_code_forbidden_import_should_not_raise_on_allowed_packages():
    code = dedent_triple_quote_str("""
        import pandas as pd
        import numpy as np
        from scipy.stats import chi2_contingency
        """)
    CodeRunner().run(code)


def test_run_code_wrong_import():
    code = dedent_triple_quote_str("""
        from xxx import yyy
        """)
    error = CodeRunner().run(code)[3]
    assert isinstance(error, FailedRunningCode)
    assert error.exception.fromlist == ('yyy',)


code = dedent_triple_quote_str("""
    with open('test.txt', 'w') as f:
        f.write('hello')
    """)


def test_run_code_raises_on_unallowed_open_files(tmpdir):
    error = CodeRunner(allowed_open_write_files=[], run_folder=tmpdir).run(code)[3]
    assert isinstance(error, FailedRunningCode)
    assert isinstance(error.exception, CodeWriteForbiddenFile)
    linenos_lines, msg = error.get_lineno_line_message()
    assert linenos_lines == [(1, "with open('test.txt', 'w') as f:")]


def test_run_code_raises_on_unallowed_created_files(tmpdir):
    error = CodeRunner(allowed_open_write_files='all', run_folder=tmpdir).run(code)[3]
    assert isinstance(error, FailedRunningCode)
    assert isinstance(error.exception, UnAllowedFilesCreated)
    lineno_line, msg = error.get_lineno_line_message()
    assert lineno_line == []


def test_run_code_allows_allowed_files(tmpdir):
    os.chdir(tmpdir)
    CodeRunner(allowed_open_write_files=['test.txt'], output_file_requirements=None).run(code)


def test_run_code_that_creates_pvalues_using_f_oneway(tmpdir):
    code = dedent_triple_quote_str("""
        import pickle
        import pandas as pd 
        from scipy.stats import f_oneway
        all_mses = [[1, 2, 3], [4, 5, 6], [7, 8, 9], 
                    pd.Series([10, 11, 12, 13 ,14]), pd.Series([15, 16, 17, 18, 19]), pd.Series([20, 21, 22, 23, 24])]
        f_oneway_result = f_oneway(*all_mses)
        additional_results = {'f_score': f_oneway_result.statistic, 'p_value': f_oneway_result.pvalue}
        with open('additional_results.pkl', 'wb') as f:
            pickle.dump(additional_results, f)
        """)
    with OverrideStatisticsPackages():
        error = CodeRunner(run_folder=tmpdir,
                           allowed_open_write_files=None,
                           output_file_requirements=OutputFileRequirements(
                            (DictPickleContentOutputFileRequirement('additional_results.pkl', 1),)), ).run(code)[3]
        if error is not None:
            raise error
        assert os.path.exists(tmpdir / 'additional_results.pkl')
        import pickle
        p_value = pickle.load(open(tmpdir / 'additional_results.pkl', 'rb'))['p_value']
        assert p_value.created_by == 'f_oneway'


def test_run_code_with_sklearn_class_with_no_random_state_defined():
    code = """
from sklearn.linear_model import ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
# initialize models without setting random_state
models = {'Random Forest': RandomForestRegressor(), 'Elastic Net': ElasticNet(), 'Neural network': MLPRegressor()}
# check if models are initialized with `random_state=0` by using the replacer we created
for model in models.keys():
    if hasattr(models[model], 'random_state'):
        assert models[model].random_state == 0, f'{model} is not initialized with random_state=0'
"""
    with SklearnRandomStateOverride():
        error = CodeRunner().run(code)[3]
        if error is not None:
            raise error


def test_global_random_seed():
    # code that uses random and numpy.random
    code = dedent_triple_quote_str("""
        import random
        import numpy as np
        def func():
            a = random.random()
            assert a != random.random()
            b = np.random.random()
            assert b != np.random.random()
            return a, b        
        """)
    for seed in [0, 1, None]:
        with SetRandomSeeds(random_seed=seed):
            a1, b1 = CallFuncCodeRunner().run(code)[0]
        with SetRandomSeeds(random_seed=seed):
            a2, b2 = CallFuncCodeRunner().run(code)[0]
        if seed is None:
            assert a1 != a2
            assert b1 != b2
        else:
            assert a1 == a2
            assert b1 == b2


@pytest.mark.parametrize("MLPclass, hidden_layer_sizes, expected_err, contains", (
        ('MLPRegressor', (50,), None, ''),
        ('MLPClassifier', (50, 50, 50), RunIssue, '(3) is too large!'),
        ('MLPRegressor', (200,), RunIssue, 'has a layer (0) with too many neurons'),)
                         )
def test_run_code_with_sklearn_nn_with_too_many_layers(MLPclass, hidden_layer_sizes, expected_err, contains):
    code = f"""
from sklearn.neural_network import {MLPclass}
mlp = {MLPclass}(hidden_layer_sizes={hidden_layer_sizes})
"""
    error = CodeRunner(additional_contexts={'SklearnNNSizeOverride': SklearnNNSizeOverride()}).run(code)[3]
    if expected_err is None:
        assert error is None
    else:
        if error is None:
            raise AssertionError(f"Expected a {expected_err} warning, but got None.")
        assert isinstance(error, expected_err)
        assert contains in str(error)
