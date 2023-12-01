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
    WRITING_RESULTS = Stage("writing_results")
    WRITING_TITLE_AND_ABSTRACT = Stage("writing_title_and_abstract")
    WRITING_METHODS = Stage("writing_methods")
    WRITING_INTRODUCTION = Stage("writing_introduction")
    WRITING_DISCUSSION = Stage("writing_discussion")
    CITATIONS = Stage("citations")
    TABLES = Stage("tables")


SECTION_NAMES_TO_WRITING_STAGES = {
    "title_and_abstract": ScientificStages.WRITING_TITLE_AND_ABSTRACT,
    "introduction": ScientificStages.WRITING_INTRODUCTION,
    "methods": ScientificStages.WRITING_METHODS,
    "results": ScientificStages.WRITING_RESULTS,
    "discussion": ScientificStages.WRITING_DISCUSSION,
}
