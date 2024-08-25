from dataclasses import dataclass

from pytest import fixture

from data_to_paper.base_products.file_descriptions import DataFileDescription
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER
from data_to_paper.research_types.hypothesis_testing.reviewing_steps import GoalReviewGPT


@dataclass(frozen=True)
class MockDataFileDescription(DataFileDescription):
    header: str = ''

    def get_file_header(self, number_of_lines: int = 1):
        return self.header


@fixture()
def data_file_descriptions():
    return DataFileDescriptions(
        [MockDataFileDescription(file_path='BIRTH_RECORDS.csv', description='birth records',
                                 header='patient_id, gender\n 2648, F\n 2649, M\n')],
        data_folder='.')


@fixture()
def goal_reviewer(data_file_descriptions, actions_and_conversations):
    return GoalReviewGPT(
        actions_and_conversations=actions_and_conversations,
        suppress_printing_other_conversation=False,
        products=ScientificProducts(
            data_file_descriptions=data_file_descriptions,
        )
    )


@OPENAI_SERVER_CALLER.record_or_replay()
def test_goal_reviewer(goal_reviewer):
    research_goal = goal_reviewer.run_and_get_valid_result()

    # depending on openai response, these conditions may not be necessarily be met:
    assert 'birth' in research_goal
