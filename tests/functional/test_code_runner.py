import pytest
import os

from g3pt.run_gpt_code.code_runner import CodeRunner, FailedExtractingCode, FailedLoadingOutput
from g3pt.run_gpt_code.exceptions import CodeUsesForbiddenFunctions, FailedRunningCode

OUTPUT_FILE = "output.txt"

code_encoded_in_response = f'with open("{OUTPUT_FILE}", "w") as f:\n    f.write("hello")'

valid_response = f"""
Here is a code that does what you want:
```python
{code_encoded_in_response}
```
"""

no_code_response = """
I cannot write a code for you.
"""

two_codes_response = f"""
Here is a code that does what you want:
```python
{code_encoded_in_response}
```

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

code_not_creating_file = f"""
This code calculates, but does not write to file:
```python
txt = 'hello'
```
"""


def test_runner_correctly_extract_code_to_run():
    assert CodeRunner(response=valid_response, output_file='output.txt').extract_code() == code_encoded_in_response


def test_runner_correctly_run_extracted_code(tmpdir):
    os.chdir(tmpdir)
    assert CodeRunner(response=valid_response, output_file='output.txt').run_code().output == 'hello'


def test_runner_raises_when_output_not_found(tmpdir):
    os.chdir(tmpdir)
    with pytest.raises(FailedLoadingOutput):
        CodeRunner(response=code_not_creating_file, output_file='wrong_output.txt').run_code()


def test_runner_raises_when_code_writes_to_wrong_file(tmpdir):
    os.chdir(tmpdir)
    with pytest.raises(FailedRunningCode):
        CodeRunner(response=valid_response, output_file='wrong_output.txt').run_code()


def test_runner_raises_when_no_code_is_found():
    with pytest.raises(FailedExtractingCode):
        CodeRunner(response=no_code_response, output_file='output.txt').run_code()


def test_runner_raises_when_multiple_codes_are_found():
    with pytest.raises(FailedExtractingCode):
        CodeRunner(response=two_codes_response, output_file='output.txt').run_code()


def test_runner_raises_when_code_use_forbidden_functions():
    try:
        CodeRunner(response=code_using_print, output_file='output.txt').run_code()
    except FailedRunningCode as e:
        assert isinstance(e.exception, CodeUsesForbiddenFunctions)
        assert 'print' == e.exception.func
    else:
        assert False, "FailedRunningCode was not raised"
