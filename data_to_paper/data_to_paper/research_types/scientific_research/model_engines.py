from data_to_paper.servers.model_engine import ModelEngine

TYPE_OF_MODELS = 'closed'

if TYPE_OF_MODELS == 'closed':
    ModelEngine.DEFAULT = ModelEngine.GPT35_TURBO
    CLASSES_TO_MODEL_ENGINES = {
        "DataExplorationCodeProductsGPT": ModelEngine.GPT4,
        "DataAnalysisCodeProductsGPT": ModelEngine.GPT4,
        "CreateTablesCodeProductsGPT": ModelEngine.GPT4,
        "GetMostSimilarCitations": ModelEngine.GPT4,
        "IsGoalOK": ModelEngine.GPT4,
        "TablesReviewBackgroundProductsConverser": ModelEngine.GPT4,
        "IntroductionSectionWriterReviewGPT": ModelEngine.GPT4,
        "DiscussionSectionWriterReviewGPT": ModelEngine.GPT4,
    }
elif TYPE_OF_MODELS == 'open':
    ModelEngine.DEFAULT = ModelEngine.LLAMA_2_70b
    CLASSES_TO_MODEL_ENGINES = {
        "DataExplorationCodeProductsGPT": ModelEngine.GPT4,
        "DataAnalysisCodeProductsGPT": ModelEngine.CODELLAMA,
        "CreateTablesCodeProductsGPT": ModelEngine.CODELLAMA,
        "GetMostSimilarCitations": ModelEngine.LLAMA_2_70b,
        "IsGoalOK": ModelEngine.LLAMA_2_70b,
        "TablesReviewBackgroundProductsConverser": ModelEngine.LLAMA_2_70b,
        "IntroductionSectionWriterReviewGPT": ModelEngine.LLAMA_2_70b,
        "DiscussionSectionWriterReviewGPT": ModelEngine.LLAMA_2_70b,
    }
else:
    raise ValueError(f'Unknown type of models: {TYPE_OF_MODELS}')


def get_model_engine_for_class(class_: type) -> ModelEngine:
    return CLASSES_TO_MODEL_ENGINES[class_.__name__]
