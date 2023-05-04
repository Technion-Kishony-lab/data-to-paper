from g3pt.conversation.conversation import OPENAI_SERVER_CALLER
from g3pt.gpt_interactors.dual_converser import ReviewDialogDualConverserGPT


@OPENAI_SERVER_CALLER.record_or_replay()
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
