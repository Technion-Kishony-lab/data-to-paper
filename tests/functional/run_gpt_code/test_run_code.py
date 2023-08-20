import os
import time

import pytest
from _pytest.python_api import raises

from data_to_paper.run_gpt_code.dynamic_code import RunCode, CODE_MODULE, FailedRunningCode
from data_to_paper.run_gpt_code.exceptions import CodeUsesForbiddenFunctions, \
    CodeWriteForbiddenFile, CodeImportForbiddenModule, UnAllowedFilesCreated
from data_to_paper.run_gpt_code.types import OutputFileRequirements
from data_to_paper.utils import dedent_triple_quote_str


def test_run_code_on_legit_code():
    code = dedent_triple_quote_str("""
        def f():
            return 'hello'
        """)
    RunCode().run(code)
    assert CODE_MODULE.f() == 'hello'


def test_run_code_correctly_reports_exception():
    code = dedent_triple_quote_str("""
        # line 1
        # line 2
        raise Exception('error')
        # line 4
        """)
    with raises(FailedRunningCode) as e:
        RunCode().run(code)

    error = e.value
    assert error.exception.args[0] == 'error'
    linenos_lines, msg = error.get_lineno_line_message()
    assert linenos_lines == [(3, "raise Exception('error')")]


def test_run_code_catches_warning():
    code = dedent_triple_quote_str("""
        import warnings
        warnings.warn('be careful', UserWarning)
        """)
    with pytest.raises(FailedRunningCode) as e:
        RunCode(warnings_to_raise=[UserWarning]).run(code)
    error = e.value
    lineno_line, msg = error.get_lineno_line_message()
    assert msg == 'be careful'
    assert lineno_line == [(2, "warnings.warn('be careful', UserWarning)")]


def test_run_code_correctly_reports_exception_from_func():
    code = dedent_triple_quote_str("""
        def func():
            raise Exception('stupid error')
        func()
        """)
    with pytest.raises(FailedRunningCode) as e:
        RunCode().run(code)
    error = e.value
    assert error.exception.args[0] == 'stupid error'
    linenos_lines, msg = error.get_lineno_line_message()
    assert linenos_lines == [(3, 'func()'), (2, "raise Exception('stupid error')")]
    msg = error.get_traceback_message()
    assert 'func()' in msg
    assert "raise Exception('stupid error')" in msg
    assert 'stupid error' in msg


def test_run_code_timeout():
    code = dedent_triple_quote_str("""
        import time
        # line 2
        time.sleep(2)
        # line 4
        """)
    with pytest.raises(FailedRunningCode) as e:
        RunCode(timeout_sec=1).run(code)
    error = e.value
    assert isinstance(error.exception, TimeoutError)
    lineno_lines, msg = error.get_lineno_line_message()
    assert lineno_lines == [(3, 'time.sleep(2)')]


@pytest.mark.parametrize("forbidden_call", ['input', 'exit', 'quit', 'eval'])
def test_run_code_forbidden_functions(forbidden_call):
    time.sleep(0.1)
    code = dedent_triple_quote_str("""
        a = 1
        {}()
        """).format(forbidden_call)
    with pytest.raises(FailedRunningCode) as e:
        RunCode().run(code)
    error = e.value
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
    result, created_files, issues, contexts = RunCode().run(code)
    assert 'print' in issues[0].issue


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
    with pytest.raises(FailedRunningCode) as e:
        RunCode().run(code)
    error = e.value
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
    RunCode().run(code)


def test_run_code_wrong_import():
    code = dedent_triple_quote_str("""
        from xxx import yyy
        """)
    with raises(FailedRunningCode) as e:
        RunCode().run(code)
    error = e.value
    assert error.exception.fromlist == ('yyy', )


code = dedent_triple_quote_str("""
    with open('test.txt', 'w') as f:
        f.write('hello')
    """)


def test_run_code_raises_on_unallowed_open_files(tmpdir):
    with pytest.raises(FailedRunningCode) as e:
        RunCode(allowed_open_write_files=[], run_folder=tmpdir).run(code)
    error = e.value
    assert isinstance(error.exception, CodeWriteForbiddenFile)
    linenos_lines, msg = error.get_lineno_line_message()
    assert linenos_lines == [(1, "with open('test.txt', 'w') as f:")]


def test_run_code_raises_on_unallowed_created_files(tmpdir):
    with pytest.raises(FailedRunningCode) as e:
        RunCode(allowed_open_write_files=None, run_folder=tmpdir).run(code)
    error = e.value
    assert isinstance(error.exception, UnAllowedFilesCreated)
    lineno_line, msg = error.get_lineno_line_message()
    assert lineno_line == []


def test_run_code_allows_allowed_files(tmpdir):
    os.chdir(tmpdir)
    RunCode(allowed_open_write_files=['test.txt'], output_file_requirements=None).run(code)
