import os
import pytest

from data_to_paper.run_gpt_code.dynamic_code import run_code_using_module_reload, CODE_MODULE, FailedRunningCode
from data_to_paper.run_gpt_code.exceptions import CodeUsesForbiddenFunctions, \
    CodeWriteForbiddenFile, CodeImportForbiddenModule
from data_to_paper.utils import dedent_triple_quote_str


def test_run_code_on_legit_code():
    code = dedent_triple_quote_str("""
        def f():
            return 'hello'
        """)
    run_code_using_module_reload(code)
    assert CODE_MODULE.f() == 'hello'


def test_run_code_correctly_reports_exception():
    code = dedent_triple_quote_str("""
        # line 1
        # line 2
        raise Exception('error')
        # line 4
        """)
    try:
        run_code_using_module_reload(code)
    except FailedRunningCode as e:
        assert e.exception.args[0] == 'error'
        assert e.tb[-1].lineno == 3
    else:
        assert False, 'Expected to fail'


def test_run_code_catches_warning():
    code = dedent_triple_quote_str("""
        import warnings
        warnings.warn('be careful', UserWarning)
        """)
    try:
        run_code_using_module_reload(code, warnings_to_raise=[UserWarning])
    except FailedRunningCode as e:
        assert e.exception.args[0] == 'be careful'
        assert e.tb[-1].lineno == 2
    else:
        assert False, 'Expected to fail'


def test_run_code_timeout():
    code = dedent_triple_quote_str("""
        import time
        # line 2
        time.sleep(2)
        # line 4
        """)
    try:
        run_code_using_module_reload(code, timeout_sec=1)
    except FailedRunningCode as e:
        assert isinstance(e.exception, TimeoutError)
        assert e.tb is None  # we currently do not get a traceback for timeout
    else:
        assert False, 'Expected to fail'


@pytest.mark.parametrize("forbidden_call", ['input', 'print', 'exit', 'quit', 'eval'])
def test_run_code_forbidden_function_exit(forbidden_call):
    code = dedent_triple_quote_str("""
        a = 1
        {}()
        """).format(forbidden_call)
    try:
        run_code_using_module_reload(code)
    except FailedRunningCode as e:
        assert isinstance(e.exception, CodeUsesForbiddenFunctions)
        assert e.tb[-1].lineno == 2
    else:
        assert False, 'Expected to fail'


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
    try:
        run_code_using_module_reload(code)
    except FailedRunningCode as e:
        assert isinstance(e.exception, CodeImportForbiddenModule)
        assert e.exception.module == module_name
        assert e.tb[-1].lineno == 3
    else:
        assert False, 'Expected to fail'


def test_run_code_forbidden_import_should_not_raise_on_allowed_packages():
    code = dedent_triple_quote_str("""
        import pandas as pd
        import numpy as np
        from scipy.stats import chi2_contingency
        """)
    try:
        run_code_using_module_reload(code)
    except Exception as e:
        assert False, 'Should not raise, got {}'.format(e)
    else:
        assert True


def test_run_code_wrong_import():
    code = dedent_triple_quote_str("""
        from xxx import yyy
        """)
    try:
        run_code_using_module_reload(code)
    except FailedRunningCode as e:
        assert e.exception.fromlist == ('yyy', )


code = dedent_triple_quote_str("""
    with open('test.txt', 'w') as f:
        f.write('hello')
    """)


def test_run_code_raises_on_unallowed_files(tmpdir):
    try:
        os.chdir(tmpdir)
        run_code_using_module_reload(code, allowed_write_files=[])
    except FailedRunningCode as e:
        assert isinstance(e.exception, CodeWriteForbiddenFile)
        assert e.tb[-1].lineno == 1
    else:
        assert False, 'Expected to fail'


def test_run_code_allows_allowed_files(tmpdir):
    os.chdir(tmpdir)
    run_code_using_module_reload(code, allowed_write_files=['test.txt'])
