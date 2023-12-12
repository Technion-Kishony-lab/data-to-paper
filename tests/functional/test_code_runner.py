import pytest
import os

from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.exceptions import CodeUsesForbiddenFunctions, FailedRunningCode, CodeTimeoutException, \
    CodeWriteForbiddenFile
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

code_runs_more_than_3_seconds = f"""
This code runs more than 3 seconds:
```python
import time
time.sleep(4)
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

def test_runner_raise_code_timeout_exception(tmpdir):
    with pytest.raises(CodeTimeoutException) as e:
        CodeRunner(response=code_runs_more_than_3_seconds,
                   timeout_sec=3,
                   ).run_code_in_separate_process()
    assert f"3 seconds" in str(e.value)

