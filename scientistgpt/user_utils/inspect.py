from scientistgpt import Conversation


def view_saved_conversation(filename: str):
    Conversation.from_file(filename).print_all_messages()
