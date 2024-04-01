from data_to_paper.base_steps.dual_converser import ReviewDialogDualConverserGPT
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER


@OPENAI_SERVER_CALLER.record_or_replay()
def test_role_reversal_dialog_converser(actions_and_conversations):
    converser = ReviewDialogDualConverserGPT(
        actions_and_conversations=actions_and_conversations,
        performer='scientist',
        reviewer='scientific reviewer',
        conversation_name='scientist',
        web_conversation_name=None,
        other_conversation_name='scientific reviewer',
        goal_noun='a one-paragraph summary on the solar system',
        goal_verb='write',
    )
    converser.initialize_and_run_dialog()
