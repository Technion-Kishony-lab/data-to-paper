from data_to_paper.conversation.stage import Stage


class DemoStages(Stage):
    DATA = ("Get Data", False)
    GOAL = ("Set Goal", False)
    CODE = ("Write Code", True)
    WRITING = ("Write Abstract", True)
    COMPILE = ("Compile pdf", False)
