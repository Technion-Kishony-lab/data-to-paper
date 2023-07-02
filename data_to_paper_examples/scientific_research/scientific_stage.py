from data_to_paper.conversation.stage import Stages, Stage


class ScientificStages(Stages):
    DATA = Stage("data")
    EXPLORATION = Stage("exploration")
    GOAL = Stage("goal")
    PREPROCESSING = Stage("preprocessing")
    PLAN = Stage("plan")
    # GOAL_AND_PLAN = Stage("goal_and_plan")
    LITERATURE_REVIEW_AND_SCOPE = Stage("literature_review_and_scope")
    CODE = Stage("code")
    INTERPRETATION = Stage("interpretation")
    WRITING = Stage("writing")
    CITATIONS = Stage("citations")
    TABLES = Stage("tables")
