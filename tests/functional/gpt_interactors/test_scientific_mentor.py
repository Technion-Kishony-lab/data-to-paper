import pytest

from scientistgpt import ScientistGPT
from scientistgpt.conversation.conversation import OPENAI_SERVER_CALLER
from scientistgpt.data_file_description import DataFileDescription


class TestDataFileDescription(DataFileDescription):
    def get_file_header(self, num_lines: int = 4):
        return ''


@pytest.mark.skip
@OPENAI_SERVER_CALLER.record_or_replay()
def test_scientific_mentor():
    runner = ScientistGPT(
        data_file_descriptions=[DataFileDescription(
                file_path='data.csv',
                description='a csv file with columns "gender" (F/M) and "height" (in cm) representing '
                            'the height of a person.')],
        goal_description='I am interested whether there is a significant height difference between females and males')
    runner.run_all()
