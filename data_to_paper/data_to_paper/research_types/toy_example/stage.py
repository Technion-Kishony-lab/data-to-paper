from data_to_paper.conversation.stage import Stage


class DemoStages(Stage):
    DATA = ("Get Data", True)
    GOAL = ("Set Goal", True)
    CODE = ("Write Code", True)
    WRITING = ("Write Abstract", True)
    COMPILE = ("Compile pdf", True)
