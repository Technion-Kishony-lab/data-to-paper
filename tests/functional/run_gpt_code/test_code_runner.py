import pytest
import os

from data_to_paper.run_gpt_code.code_runner_wrapper import CodeRunnerWrapper
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.exceptions import CodeUsesForbiddenFunctions, FailedRunningCode
from data_to_paper.run_gpt_code.code_utils import FailedExtractingBlock
from data_to_paper.run_gpt_code.extract_and_check_code import CodeExtractor

OUTPUT_FILE = "output.txt"

code_encoded_in_response = f'\nwith open("{OUTPUT_FILE}", "w") as f:\n    f.write("hello")\n'

valid_response = f"""
Here is a code that does what you want:
```python{code_encoded_in_response}```
"""

no_code_response = """
I cannot write a code for you.
"""

two_codes_response = f"""
Here is a code that does what you want:
```python{code_encoded_in_response}```

to run it you should first set:
```python
txt = 'hello'
```
"""

code_using_print = f"""
print('hello')
"""

code_using_input = f"""
a = input('choose: ')
"""

code_not_creating_file = f"""
This code calculates, but does not write to file:
```python
txt = 'hello'
```
"""

code_runs_more_than_1_second = f"""
import time
time.sleep(100)
"""


def test_runner_correctly_extract_code_to_run():
    assert CodeExtractor().get_modified_code_and_num_added_lines(valid_response)[0] \
           == code_encoded_in_response


def test_runner_correctly_run_extracted_code(tmpdir):
    os.chdir(tmpdir)
    result = CodeRunnerWrapper(code=code_encoded_in_response,
                               code_runner=CodeRunner(allowed_open_write_files=('output.txt',), run_folder=tmpdir),
                               ).run_code_in_separate_process()
    created_files = result[1]
    assert 'output.txt' in created_files


def test_runner_raises_when_code_writes_to_wrong_file(tmpdir):
    os.chdir(tmpdir)
    _, _, _, exception = \
        CodeRunnerWrapper(
            code=code_encoded_in_response,
            code_runner=CodeRunner(
                allowed_open_write_files=('wrong_output.txt', )),
        ).run_code_in_separate_process()
    assert isinstance(exception, FailedRunningCode)


def test_extractor_raises_when_no_code_is_found():
    with pytest.raises(FailedExtractingBlock):
        CodeExtractor().get_modified_code_and_num_added_lines(no_code_response)


def test_extractor_raises_when_multiple_codes_are_found():
    with pytest.raises(FailedExtractingBlock):
        CodeExtractor().get_modified_code_and_num_added_lines(two_codes_response)


def test_runner_raises_when_code_use_forbidden_functions():
    _, _, _, exception = CodeRunner().run(code_using_input)
    assert isinstance(exception, FailedRunningCode)
    assert isinstance(exception.exception, CodeUsesForbiddenFunctions)
    assert 'input' == exception.exception.func


def test_runner_create_issue_on_print():
    _, _, multi_context, exception = CodeRunner().run(code_using_print)
    assert 'print' in multi_context.issues[0].issue


def test_runner_raise_code_timeout_exception():
    _, _, _, exception = \
        CodeRunnerWrapper(timeout_sec=1, code=code_runs_more_than_1_second).run_code_in_separate_process()
    assert f"1 seconds" in str(exception.exception)


code_multi_process_gipc = """
import gipc
import time
p = gipc.start_process(target=time.sleep, args=(40,))
p.join()
"""

code_multi_process_threading = """
import threading
import time
p = threading.Thread(target=time.sleep, args=(40,))
p.start()
p.join()
"""

code_multi_process_multiprocessing = """
import multiprocessing
import time
p = multiprocessing.Process(target=time.sleep, args=(40,))
p.start()
p.join()
"""


code_multi_process_sklearn = """
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
"""


code_same_process = """
import time
time.sleep(40)
"""

timeout_sec = 3


@pytest.mark.parametrize("code", [
    # code_multi_process_gipc,
    code_multi_process_threading,
    code_multi_process_multiprocessing,
    code_multi_process_sklearn,
    code_multi_process_sklearn,
    code_same_process,
])
def test_run_code_timeout_multiprocessing(code):
    """
    is_internal:
        False if by CodeRunnerWrapper
        True if the timeout is by CodeRunner (1 sec earlier).
    """
    _, _, _, exception = \
        CodeRunnerWrapper(code=code,
                          timeout_sec=timeout_sec,
                          ).run_code_in_separate_process()
    assert isinstance(exception, FailedRunningCode)
    assert isinstance(exception.exception, TimeoutError)
    lineno_lines, msg = exception.get_lineno_line_message()
    assert msg == f'Code timeout after {timeout_sec} seconds.'
