import os.path
import pickle

import pandas as pd
import pytest

from data_to_paper.research_types.hypothesis_testing.coding.analysis.utils import get_pickle_dump_attr_replacer
from data_to_paper.run_gpt_code.run_issues import RunIssue
from data_to_paper.utils.file_utils import run_in_directory

filename = 'additional_results.pkl'

default_message = 'string keys and values that are basic types'


@pytest.mark.parametrize('obj, issue', [
    ({'a': 5}, None),
    ({7: 5}, default_message),
    ({'a': [1, 3]}, None),
    ({'a': [[1]]}, 'I found: `list`'),
    ('a str', default_message),
    (pd.DataFrame({'a': [2]}), default_message),
    ({'df': pd.DataFrame({'a': [2]})}, 'DataFrame'),
    ({'long': 'a' * 10000}, 'too large'),

])
def test_additional_results_raise_issue(tmpdir, obj, issue):
    with run_in_directory(tmpdir):
        try:
            with get_pickle_dump_attr_replacer():
                with open(filename, 'wb') as f:
                    pickle.dump(obj, f)
        except RunIssue as ri:
            assert issue is not None
            if issue:
                assert issue in ri.issue
            else:
                print(ri.issue)
            assert not os.path.exists(filename)
        else:
            assert issue is None
            assert os.path.exists(filename)
