import time

import pytest
from pytest import raises

from data_to_paper.run_gpt_code.code_runner import is_serializable
from data_to_paper.run_gpt_code.timeout_context import timeout_context, TimeoutWindowsContext, TimeoutUnixContext


def test_timeout_context_not_raising():
    with timeout_context(1):
        time.sleep(0.1)


def test_timeout_context_raising():
    with raises(TimeoutError):
        with timeout_context(1):
            time.sleep(2)


@pytest.mark.parametrize("context_cls", [TimeoutWindowsContext, TimeoutUnixContext])
def test_timeout_context_is_serializable(context_cls):
    context = context_cls(seconds=1)
    try:
        with context:
            pass
    except Exception:
        pass
    assert is_serializable(context)
