import pytest
import os

from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.exceptions import CodeUsesForbiddenFunctions, FailedRunningCode
from data_to_paper.run_gpt_code.code_utils import FailedExtractingBlock
from data_to_paper.run_gpt_code.types import ContentOutputFileRequirement

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


def test_runner_correctly_extract_code_to_run():
    assert CodeRunner(response=valid_response,
                      output_file_requirements=(ContentOutputFileRequirement('output.txt'), ),
                      ).extract_code() == code_encoded_in_response


def test_runner_correctly_run_extracted_code(tmpdir):
    os.chdir(tmpdir)
    assert CodeRunner(response=valid_response,
                      output_file_requirements=(ContentOutputFileRequirement('output.txt'),),
                      ).run_code()[0].get_single_output() == 'hello'


def test_runner_raises_when_code_writes_to_wrong_file(tmpdir):
    os.chdir(tmpdir)
    with pytest.raises(FailedRunningCode):
        CodeRunner(response=valid_response,
                   output_file_requirements=(ContentOutputFileRequirement('wrong_output.txt'),),
                   ).run_code()


def test_runner_raises_when_no_code_is_found():
    with pytest.raises(FailedExtractingBlock):
        CodeRunner(response=no_code_response,
                   output_file_requirements=(ContentOutputFileRequirement('output.txt'),),
                   ).run_code()


def test_runner_raises_when_multiple_codes_are_found():
    with pytest.raises(FailedExtractingBlock):
        CodeRunner(response=two_codes_response,
                   output_file_requirements=(ContentOutputFileRequirement('output.txt'),),
                   ).run_code()


def test_runner_raises_when_code_use_forbidden_functions():
    try:
        CodeRunner(response=code_using_input,
                   output_file_requirements=(ContentOutputFileRequirement('output.txt'),),
                   ).run_code()
    except FailedRunningCode as e:
        assert isinstance(e.exception, CodeUsesForbiddenFunctions)
        assert 'input' == e.exception.func
    else:
        assert False, "FailedRunningCode was not raised"


def test_runner_create_issue_on_print():
    _, issue_collector = CodeRunner(response=code_using_print,
                                    output_file_requirements=(ContentOutputFileRequirement('output.txt'),),
                                    ).run_code()
    assert 'print' in issue_collector.issues[0].issue
