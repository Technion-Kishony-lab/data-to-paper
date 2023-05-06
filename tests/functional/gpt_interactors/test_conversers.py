from scientistgpt.base_steps.dual_converser import ReviewDialogDualConverserGPT
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER


@OPENAI_SERVER_CALLER.record_or_replay()
def test_role_reversal_dialog_converser():
    converser = ReviewDialogDualConverserGPT(
        performer='scientist',
        reviewer='scientific reviewer',
        conversation_name='scientist',
        other_conversation_name='scientific reviewer',
        goal_noun='a one-paragraph summary on the solar system',
        goal_verb='write',
    )
    print()
    converser.initialize_and_run_dialog()
