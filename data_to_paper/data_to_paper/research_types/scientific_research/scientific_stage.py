from data_to_paper.conversation.stage import Stages, Stage


class ScientificStages(Stages):
    DATA = Stage("data")
    EXPLORATION = Stage("exploration")
    GOAL = Stage("goal")
    LITERATURE_REVIEW_GOAL = Stage("literature_review_goal")
    ASSESS_NOVELTY = Stage("assess_novelty")
    PLAN = Stage("plan")
    # GOAL_AND_PLAN = Stage("goal_and_plan")
    CODE = Stage("code")
    TABLES = Stage("tables")
    INTERPRETATION = Stage("interpretation")
    LITERATURE_REVIEW_WRITING = Stage("literature_review_writing")
    WRITING = Stage("writing")
    WRITING_RESULTS = Stage("writing_results")
    WRITING_TITLE_AND_ABSTRACT = Stage("writing_title_and_abstract")
    WRITING_METHODS = Stage("writing_methods")
    WRITING_INTRODUCTION = Stage("writing_introduction")
    WRITING_DISCUSSION = Stage("writing_discussion")


SECTION_NAMES_TO_WRITING_STAGES = {
    "title_and_abstract": ScientificStages.WRITING_TITLE_AND_ABSTRACT,
    "introduction": ScientificStages.WRITING_INTRODUCTION,
    "methods": ScientificStages.WRITING_METHODS,
    "results": ScientificStages.WRITING_RESULTS,
    "discussion": ScientificStages.WRITING_DISCUSSION,
}


SCIENTIFIC_STAGES_TO_NICE_NAMES = {
    ScientificStages.DATA: "Get Data",
    ScientificStages.EXPLORATION: "Data Exploration",
    ScientificStages.GOAL: "Research Goal",
    ScientificStages.LITERATURE_REVIEW_GOAL: "Lit. Review I",
    ScientificStages.ASSESS_NOVELTY: "Assess Novelty",
    ScientificStages.PLAN: "Hypothesis & Plan",
    ScientificStages.CODE: "Data Analysis",
    ScientificStages.TABLES: "Create Tables",
    ScientificStages.INTERPRETATION: "Draft abstract",
    ScientificStages.LITERATURE_REVIEW_WRITING: "Lit. Review II",
    ScientificStages.WRITING_RESULTS: "Write Results",
    ScientificStages.WRITING_TITLE_AND_ABSTRACT: "Abstract",
    ScientificStages.WRITING_METHODS: "Methods",
    ScientificStages.WRITING_INTRODUCTION: "Introduction",
    ScientificStages.WRITING_DISCUSSION: "Discussion",
    ScientificStages.FINISHED: "Compile Paper",
}
