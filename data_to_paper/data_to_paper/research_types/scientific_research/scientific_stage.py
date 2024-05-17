from data_to_paper.conversation.stage import Stage


class ScientificStage(Stage):
    DATA = "Get Data"
    EXPLORATION = "Data Exploration"
    GOAL = "Research Goal"
    LITERATURE_REVIEW_GOAL = "Lit. Review I"
    ASSESS_NOVELTY = "Assess Novelty"
    PLAN = "Hypothesis & Plan"
    CODE = "Data Analysis"
    TABLES = "Create Tables"
    INTERPRETATION = "Draft abstract"
    LITERATURE_REVIEW_WRITING = "Lit. Review II"
    WRITING_RESULTS = "Results"
    WRITING_TITLE_AND_ABSTRACT = "Title and Abstract"
    WRITING_METHODS = "Methods"
    WRITING_INTRODUCTION = "Introduction"
    WRITING_DISCUSSION = "Discussion"
    COMPILE = "Compile Paper"


SECTION_NAMES_TO_WRITING_STAGES = {
    "title_and_abstract": ScientificStage.WRITING_TITLE_AND_ABSTRACT,
    "introduction": ScientificStage.WRITING_INTRODUCTION,
    "methods": ScientificStage.WRITING_METHODS,
    "results": ScientificStage.WRITING_RESULTS,
    "discussion": ScientificStage.WRITING_DISCUSSION,
}
