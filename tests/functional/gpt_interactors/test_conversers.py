from scientistgpt.gpt_interactors.dual_converser import ReviewDialogDualConverserGPT
from tests.utils import record_or_replay_openai


@record_or_replay_openai()
def test_role_reversal_dialog_converser():
    converser = ReviewDialogDualConverserGPT(
        reviewee='scientist',
        reviewer='scientific reviewer',
        conversation_name='scientist',
        other_conversation_name='scientific reviewer',
        goal_noun='a one-paragraph summary on the solar system',
        goal_verb='write',
    )
    print()
    converser.initialize_and_run_dialog()
