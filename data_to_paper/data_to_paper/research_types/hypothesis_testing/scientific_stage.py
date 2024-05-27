from data_to_paper.conversation.stage import Stage


class ScientificStage(Stage):
    DATA = ("Get Data", False)
    EXPLORATION = ("Data Exploration", True)
    GOAL = ("Research Goal", True)
    LITERATURE_REVIEW_GOAL = ("Lit. Review I", False)
    ASSESS_NOVELTY = ("Assess Novelty", False)
    PLAN = ("Hypothesis & Plan", True)
    CODE = ("Data Analysis", True)
    DISPLAYITEMS = ("Tables/Figures", True)
    INTERPRETATION = ("Draft abstract", True)
    LITERATURE_REVIEW_WRITING = ("Lit. Review II", True)
    WRITING_RESULTS = ("Results", True)
    WRITING_TITLE_AND_ABSTRACT = ("Title and Abstract", True)
    WRITING_METHODS = ("Methods", True)
    WRITING_INTRODUCTION = ("Introduction", True)
    WRITING_DISCUSSION = ("Discussion", True)
    COMPILE = ("Compile Paper", False)


SECTION_NAMES_TO_WRITING_STAGES = {
    "title_and_abstract": ScientificStage.WRITING_TITLE_AND_ABSTRACT,
    "introduction": ScientificStage.WRITING_INTRODUCTION,
    "methods": ScientificStage.WRITING_METHODS,
    "results": ScientificStage.WRITING_RESULTS,
    "discussion": ScientificStage.WRITING_DISCUSSION,
}
