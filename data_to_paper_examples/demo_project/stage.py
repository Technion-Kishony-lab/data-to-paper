from data_to_paper.conversation.stage import Stages, Stage


class DemoStages(Stages):
    DATA = Stage("data")
    GOAL = Stage("goal")
    CODE = Stage("code")
    WRITING = Stage("writing")
