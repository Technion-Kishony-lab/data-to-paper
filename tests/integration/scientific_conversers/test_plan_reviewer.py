from dataclasses import dataclass

from _pytest.fixtures import fixture

from data_to_paper.researches_types.scientific_research.coding_steps import DataAnalysisCodeProductsGPT
from data_to_paper.researches_types.scientific_research.scientific_products import ScientificProducts
from data_to_paper.servers.chatgpt import OPENAI_SERVER_CALLER
from data_to_paper.researches_types.scientific_research.reviewing_steps import GoalReviewGPT, PlanReviewGPT
from data_to_paper.base_products import DataFileDescriptions, DataFileDescription


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


@fixture()
def plan_reviewer(data_file_descriptions, actions_and_conversations):
    return PlanReviewGPT(
        actions_and_conversations=actions_and_conversations,
        suppress_printing_other_conversation=False,
        products=ScientificProducts(
            data_file_descriptions=data_file_descriptions,
            research_goal='to test whether there is a gender bias in the birth records',
        )
    )


@fixture()
def code_reviewer(data_file_descriptions, actions_and_conversations):
    return DataAnalysisCodeProductsGPT(
        actions_and_conversations=actions_and_conversations,
        products=ScientificProducts(
            data_file_descriptions=data_file_descriptions,
            research_goal='to test whether there is a gender bias in the birth records',
            analysis_plan='calculate gender ratio and compare to 50%'
        )
    )


@OPENAI_SERVER_CALLER.record_or_replay()
def test_goal_reviewer(goal_reviewer):
    research_goal = goal_reviewer.run_dialog_and_get_valid_result()

    # depending on openai response, these conditions may not be necessarily be met:
    assert 'gender' in research_goal


@OPENAI_SERVER_CALLER.record_or_replay()
def test_plan_reviewer(plan_reviewer):
    plan = plan_reviewer.run_dialog_and_get_valid_result()

    # depending on openai response, these conditions may not be necessarily be met:
    assert 'male' in plan
    assert 'female' in plan
