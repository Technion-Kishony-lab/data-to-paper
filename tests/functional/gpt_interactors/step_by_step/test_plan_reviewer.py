from dataclasses import dataclass

from _pytest.fixtures import fixture

from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.projects.scientific_research.steps import GoalReviewGPT, PlanReviewGPT, ScientificCodeProductsGPT
from scientistgpt.base_steps.types import DataFileDescriptions, DataFileDescription


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
    return ScientificCodeProductsGPT(
        actions_and_conversations=actions_and_conversations,
        products=ScientificProducts(
            data_file_descriptions=data_file_descriptions,
            research_goal='to test whether there is a gender bias in the birth records',
            analysis_plan='calculate gender ratio and compare to 50%'
        )
    )


@OPENAI_SERVER_CALLER.record_or_replay()
def test_goal_reviewer(goal_reviewer):
    research_goal = goal_reviewer.initialize_and_run_dialog()

    # depending on openai response, these conditions may not be necessarily be met:
    assert 'gender' in research_goal


@OPENAI_SERVER_CALLER.record_or_replay()
def test_plan_reviewer(plan_reviewer):
    plan = plan_reviewer.initialize_and_run_dialog()

    # depending on openai response, these conditions may not be necessarily be met:
    assert 'male' in plan
    assert 'female' in plan


# TODO: this code run test is far from perfect. Need to mock the code runner.

@OPENAI_SERVER_CALLER.record_or_replay()
def test_code_reviewer(code_reviewer):
    code_and_output = code_reviewer.get_analysis_code()
    print(code_and_output)
