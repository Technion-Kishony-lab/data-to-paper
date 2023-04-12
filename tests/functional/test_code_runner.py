import pytest
import os

from _pytest.fixtures import fixture

from scientistgpt.run_gpt_code.code_runner import CodeRunner, FailedExtractingCode, FailedLoadingOutput

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


@fixture()
def valid_runner():
    return CodeRunner(response=valid_response, output_file='output.txt')


@fixture()
def invalid_file_name_runner():
    return CodeRunner(response=valid_response, output_file='wrong_output.txt')


@fixture()
def invalid_two_codes_runner():
    return CodeRunner(response=two_codes_response, output_file='output.txt')


@fixture()
def invalid_no_code_runner():
    return CodeRunner(response=no_code_response, output_file='output.txt')


def test_runner_correctly_extract_code_to_run(valid_runner):
    assert valid_runner.extract_code() == code_encoded_in_response


def test_runner_correctly_run_extracted_code(valid_runner, tmpdir):
    os.chdir(tmpdir)
    assert valid_runner.run_code().output == 'hello'


def test_runner_raises_when_output_not_found(invalid_file_name_runner, tmpdir):
    os.chdir(tmpdir)
    with pytest.raises(FailedLoadingOutput):
        invalid_file_name_runner.run_code()


def test_runner_raises_when_no_code_is_found(invalid_no_code_runner):
    with pytest.raises(FailedExtractingCode):
        invalid_no_code_runner.run_code()


def test_runner_raises_when_multiple_codes_are_found(invalid_two_codes_runner):
    with pytest.raises(FailedExtractingCode):
        invalid_two_codes_runner.run_code()
