from scientistgpt.conversation.stage import Stages, Stage


class ScientificStages(Stages):
    DATA = Stage("data")
    EXPLORATION = Stage("exploration")
    GOAL = Stage("goal")
    PREPROCESSING = Stage("preprocessing")
    PLAN = Stage("plan")
    CODE = Stage("code")
    INTERPRETATION = Stage("interpretation")
    WRITING = Stage("writing")
    CITATIONS = Stage("citations")
    TABLES = Stage("tables")
