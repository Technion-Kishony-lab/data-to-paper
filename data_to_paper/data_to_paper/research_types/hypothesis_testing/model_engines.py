from data_to_paper.servers.model_engine import ModelEngine
from collections import defaultdict

TYPE_OF_MODELS = 'openai' # 'ollama', 'deepinfra', 'ollama', 'custom'

if TYPE_OF_MODELS == 'openai':
    ModelEngine.DEFAULT = ModelEngine.GPT4o_MINI
    CLASSES_TO_MODEL_ENGINES = {
        "DataExplorationCodeProductsGPT": ModelEngine.GPT4o,
        "BaseCreateTablesCodeProductsGPT": ModelEngine.GPT4o,
        "GetMostSimilarCitations": ModelEngine.GPT4o,
        "IsGoalOK": ModelEngine.GPT4o,
        "NoveltyAssessmentReview": ModelEngine.GPT4o,
        "GoalReviewGPT": ModelEngine.GPT4o,
        'SectionWriterReviewBackgroundProductsConverser': ModelEngine.GPT4o,
        "IntroductionSectionWriterReviewGPT": ModelEngine.GPT4o,
        "DiscussionSectionWriterReviewGPT": ModelEngine.GPT4o,
    }
elif TYPE_OF_MODELS == 'deepinfra':
    ModelEngine.DEFAULT = ModelEngine.LLAMA_2_70b
    CLASSES_TO_MODEL_ENGINES = {
        "DataExplorationCodeProductsGPT": ModelEngine.GPT4,
        "BaseCreateTablesCodeProductsGPT": ModelEngine.CODELLAMA,
        "GetMostSimilarCitations": ModelEngine.LLAMA_2_70b,
        "NoveltyAssessmentReview": ModelEngine.LLAMA_2_70b,
        "IntroductionSectionWriterReviewGPT": ModelEngine.LLAMA_2_70b,
        "DiscussionSectionWriterReviewGPT": ModelEngine.LLAMA_2_70b,
    }
elif TYPE_OF_MODELS == 'ollama':
    ModelEngine.DEFAULT = ModelEngine.LLAMA3
    CLASSES_TO_MODEL_ENGINES = defaultdict(lambda: ModelEngine.LLAMA3)
elif TYPE_OF_MODELS == 'custom':
    ModelEngine.DEFAULT = ModelEngine.CUSTOM
    CLASSES_TO_MODEL_ENGINES = defaultdict(lambda: ModelEngine.CUSTOM)
else:
    raise ValueError(f'Unknown type of models: {TYPE_OF_MODELS}')


def get_model_engine_for_class(class_: type) -> ModelEngine:
    return CLASSES_TO_MODEL_ENGINES[class_.__name__]
