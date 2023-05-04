from dataclasses import dataclass

from _pytest.fixtures import fixture

from g3pt.conversation.conversation import OPENAI_SERVER_CALLER
from g3pt.gpt_interactors.step_by_step.reviewers import GoalReviewGPT, PlanReviewGPT
from g3pt.gpt_interactors.step_by_step.write_code import CodeFeedbackGPT
from g3pt.gpt_interactors.types import Products, DataFileDescriptions, DataFileDescription


@dataclass(frozen=True)
class MockDataFileDescription(DataFileDescription):
    header: str = ''

    def get_file_header(self, number_of_lines: int = 1):
        return self.header


@fixture()
def data_file_descriptions():
    return DataFileDescriptions([
        MockDataFileDescription(file_path='BIRTH_RECORDS.csv', description='birth records',
                                header='patient_id, gender\n 2648, F\n 2649, M\n')])


@fixture()
def goal_reviewer(data_file_descriptions):
    return GoalReviewGPT(
        suppress_printing_other_conversation=False,
        products=Products(
            data_file_descriptions=data_file_descriptions,
        )
    )


@fixture()
def plan_reviewer(data_file_descriptions):
    return PlanReviewGPT(
        suppress_printing_other_conversation=False,
        products=Products(
            data_file_descriptions=data_file_descriptions,
            research_goal='to test whether there is a gender bias in the birth records',
        )
    )


@fixture()
def code_reviewer(data_file_descriptions):
    return CodeFeedbackGPT(
        products=Products(
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


@OPENAI_SERVER_CALLER.record_or_replay()
def test_code_reviewer(code_reviewer):
    code_feedback = code_reviewer.get_analysis_code()
    print(code_feedback)
