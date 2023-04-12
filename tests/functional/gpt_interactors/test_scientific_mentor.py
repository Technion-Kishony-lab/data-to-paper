import pytest

from scientistgpt import ScientificGPT
from tests.utils import record_or_replay_openai


@pytest.mark.skip
@record_or_replay_openai
def test_scientific_mentor():
    runner = ScientificGPT(
        data_description='file named "data.csv" with columns "gender" (F/M) and "height" (in cm) representing '
                         'the height of a person.',
        goal_description='I am interested whether there is a significant height difference between females and males')
    runner.run_all()
