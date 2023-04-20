from scientistgpt.run_gpt_code.dynamic_code import run_code_using_module_reload, module, WARNINGS_TO_RAISE
from scientistgpt.run_gpt_code.exceptions import FailedRunningCode
from scientistgpt.utils import dedent_triple_quote_str


def test_run_code_on_legit_code():
    code = dedent_triple_quote_str("""
        def f():
            return 'hello'
        """)
    run_code_using_module_reload(code)
    assert module.f() == 'hello'


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
        raise AssertionError('Expected to fail')


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
        raise AssertionError('Expected to fail')
    finally:
        WARNINGS_TO_RAISE.remove(UserWarning)
