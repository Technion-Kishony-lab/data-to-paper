from data_to_paper.servers.model_engine import ModelEngine

CODING_MODEL = ModelEngine.GPT4o

ModelEngine.DEFAULT = ModelEngine.GPT4o_MINI
CLASSES_TO_MODEL_ENGINES = {
    "DataExplorationCodeProductsGPT": CODING_MODEL,
    "DataAnalysisCodeProductsGPT": CODING_MODEL,
    "CreateDisplayitemsCodeProductsGPT": CODING_MODEL,
    "BaseCreateTablesCodeProductsGPT": ModelEngine.GPT4o,
    "GetMostSimilarCitations": ModelEngine.GPT4o,
    "IsGoalOK": ModelEngine.GPT4o,
    "NoveltyAssessmentReview": ModelEngine.GPT4o,
    "GoalReviewGPT": ModelEngine.GPT4o,
    'SectionWriterReviewBackgroundProductsConverser': ModelEngine.GPT4o,
    "IntroductionSectionWriterReviewGPT": ModelEngine.GPT4o,
    "DiscussionSectionWriterReviewGPT": ModelEngine.GPT4o,
}


def get_model_engine_for_class(class_: type) -> ModelEngine:
    return CLASSES_TO_MODEL_ENGINES[class_.__name__]
