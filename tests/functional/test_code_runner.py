import pytest
import os

from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.exceptions import CodeUsesForbiddenFunctions, FailedRunningCode
from data_to_paper.run_gpt_code.code_utils import FailedExtractingBlock
from data_to_paper.run_gpt_code.types import TextContentOutputFileRequirement, OutputFileRequirements

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
Here is a code that does what you want:
```python
print('hello')
```
"""

code_using_input = f"""
Here is a code that does what you want:
```python
a = input('choose: ')
```
"""

code_not_creating_file = f"""
This code calculates, but does not write to file:
```python
txt = 'hello'
```
"""

code_runs_more_than_1_second = f"""
This code runs more than 3 seconds:
```python
import time
time.sleep(100)
```
"""


def test_runner_correctly_extract_code_to_run():
    assert CodeRunner(response=valid_response,
                      output_file_requirements=OutputFileRequirements([TextContentOutputFileRequirement('output.txt')]),
                      ).get_raw_code() == code_encoded_in_response


def test_runner_correctly_run_extracted_code(tmpdir):
    os.chdir(tmpdir)
    assert CodeRunner(response=valid_response,
                      output_file_requirements=OutputFileRequirements([TextContentOutputFileRequirement('output.txt')]),
                      ).run_code_in_separate_process()[0].created_files.get_single_output() == 'hello'


def test_runner_raises_when_code_writes_to_wrong_file(tmpdir):
    os.chdir(tmpdir)
    _, _, _, exception = \
        CodeRunner(
            response=valid_response,
            output_file_requirements=OutputFileRequirements([TextContentOutputFileRequirement('wrong_output.txt')]),
        ).run_code_in_separate_process()
    assert isinstance(exception, FailedRunningCode)


def test_runner_raises_when_no_code_is_found():
    with pytest.raises(FailedExtractingBlock):
        CodeRunner(
            response=no_code_response,
            output_file_requirements=OutputFileRequirements([TextContentOutputFileRequirement('output.txt')]),
        ).run_code_in_separate_process()


def test_runner_raises_when_multiple_codes_are_found():
    with pytest.raises(FailedExtractingBlock):
        CodeRunner(
            response=two_codes_response,
            output_file_requirements=OutputFileRequirements([TextContentOutputFileRequirement('output.txt')]),
        ).run_code_in_separate_process()


def test_runner_raises_when_code_use_forbidden_functions():
    _, _, _, exception = \
        CodeRunner(
            response=code_using_input,
            output_file_requirements=OutputFileRequirements([TextContentOutputFileRequirement('output.txt')]),
        ).run_code_in_separate_process()
    assert isinstance(exception, FailedRunningCode)
    assert isinstance(exception.exception, CodeUsesForbiddenFunctions)
    assert 'input' == exception.exception.func


def test_runner_create_issue_on_print():
    _, issues, _, _ = CodeRunner(
        response=code_using_print,
        output_file_requirements=OutputFileRequirements(),
    ).run_code_in_separate_process()
    assert 'print' in issues[0].issue


def test_runner_raise_code_timeout_exception():
    _, _, _, exception = \
        CodeRunner(response=code_runs_more_than_1_second,
                   timeout_sec=1,
                   ).run_code_in_separate_process()
    assert f"1 seconds" in str(exception.exception)


code_multi_process1 = """
```
import multiprocessing
import time
p = multiprocessing.Process(target=time.sleep, args=(40,))
p.start()
p.join()
```
"""

code_multi_process2 = """
`    ```
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
```
"""


@pytest.mark.parametrize("code, result", [
                         (code_multi_process1, [('6', 'p.join()')]),
                         (code_multi_process2, [('14', 'grid_search.fit(X, y)')]),])
def test_run_code_timeout_multiprocessing(code, result):
    _, _, _, exception = \
        CodeRunner(response=code,
                   timeout_sec=3,
                   allowed_read_files=None,
                   output_file_requirements=None,
                   ).run_code_in_separate_process()
    assert isinstance(exception, FailedRunningCode)
    assert isinstance(exception.exception, TimeoutError)
    lineno_lines, msg = exception.get_lineno_line_message()
    assert lineno_lines == result
    assert msg == 'Code timeout after 3 seconds.'
