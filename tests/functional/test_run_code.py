from scientistgpt.run_gpt_code.dynamic_code import run_code_using_module_reload, CODE_MODULE, WARNINGS_TO_RAISE
from scientistgpt.run_gpt_code.exceptions import FailedRunningCode
from scientistgpt.utils import dedent_triple_quote_str


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
        pass
        assert e.exception.args[0] == 'error'
        assert e.code == code
        assert e.tb[-1].lineno == 3
    else:
        assert False, 'Expected to fail'


def test_run_code_catches_warning():
    code = dedent_triple_quote_str("""
        import warnings
        warnings.warn('be careful', UserWarning)
        """)
    WARNINGS_TO_RAISE.append(UserWarning)
    try:
        run_code_using_module_reload(code)
    except FailedRunningCode as e:
        assert e.exception.args[0] == 'be careful'
        assert e.code == code
        assert e.tb[-1].lineno == 2
    else:
        assert False, 'Expected to fail'
    finally:
        WARNINGS_TO_RAISE.remove(UserWarning)


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
        assert e.code == code
        assert e.tb is None  # we currently do not get a traceback for timeout
    else:
        assert False, 'Expected to fail'
