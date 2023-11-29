from dataclasses import dataclass
from typing import List, Tuple

from data_to_paper.utils.types import IndexOrderedEnum


MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR = {
    "gpt-3.5-turbo-0613": (4096, 0.0015, 0.002),
    "gpt-3.5-turbo-16k-0613": (16384, 0.003, 0.004),
    "gpt-4": (8192, 0.03, 0.06),
    "gpt-4-1106-preview": (128000, 0.01, 0.03),
    # "gpt-4-32k": (32768, 0.06, 0.12),
    "llama-2-70b-chat-hf": (4096, 0.000001, 0.000001),
    "codellama-34b-instruct-hf": (16384, 0.000001, 0.000001),
}


class ModelEngine(IndexOrderedEnum):
    """
    Enum for the different model engines available in openai.
    Support comparison operators, according to the order of the enum.
    """
    GPT35_TURBO = "gpt-3.5-turbo-0613"  # latest version that supports better system prompt adherence
    GPT35_TURBO_16 = "gpt-3.5-turbo-16k-0613"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-1106-preview"
    # GPT4_32 = "gpt-4-32k"
    LLAMA_2 = "llama-2-70b-chat-hf"
    CODELLAMA = "codellama-34b-instruct-hf"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def __hash__(self):
        return hash(self.value)

    def get_model_with_more_strength(self):
        model =  MODELS_TO_MORE_STRENGTH[self]
        if model is None:
            raise ValueError(f"Model {self} has no stronger model")
        return model

    def get_model_with_more_context(self):
        model = MODELS_TO_MORE_CONTEXT[self]
        if model is None:
            raise ValueError(f"Model {self} has no model with more context")
        return model

    @property
    def max_tokens(self):
        return MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR[self.value][0]

    @property
    def pricing(self) -> Tuple[float, float]:
        """
        Return the pricing for the model engine.
        (in_dollar_per_token, out_dollar_per_token)
        """
        return MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR[self.value][1:]


MODELS_TO_MORE_CONTEXT = {
    ModelEngine.GPT35_TURBO_16: ModelEngine.GPT4_TURBO,
    ModelEngine.GPT35_TURBO: ModelEngine.GPT35_TURBO_16,
    ModelEngine.GPT4: ModelEngine.GPT4_TURBO,
    ModelEngine.GPT4_TURBO: None,
    ModelEngine.LLAMA_2: ModelEngine.CODELLAMA,
}


MODELS_TO_MORE_STRENGTH = {
    ModelEngine.GPT35_TURBO_16: ModelEngine.GPT4_TURBO,
    ModelEngine.GPT35_TURBO: ModelEngine.GPT4_TURBO,
    ModelEngine.GPT4: ModelEngine.GPT4_TURBO,
    ModelEngine.GPT4_TURBO: None,
    ModelEngine.LLAMA_2: ModelEngine.CODELLAMA,
}


@dataclass
class OpenaiCallParameters:
    """
    Parameters for calling OpenAI API.
    """
    model_engine: ModelEngine = None
    temperature: float = None
    max_tokens: int = None
    top_p: float = None
    frequency_penalty: float = None
    presence_penalty: float = None
    response_format: dict = None
    stop: List[str] = None

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())

    def is_all_none(self):
        return all(v is None for v in self.to_dict().values())


OPENAI_CALL_PARAMETERS_NAMES = list(OpenaiCallParameters.__dataclass_fields__.keys())

TYPE_OF_MODELS_TO_CLASSES_TO_MODEL_ENGINES = {
    "closed": {
        "Converser": ModelEngine.GPT35_TURBO,
        "DataExplorationCodeProductsGPT": ModelEngine.GPT4_TURBO,
        "DataAnalysisCodeProductsGPT": ModelEngine.GPT4_TURBO,
        "CreateTablesCodeProductsGPT": ModelEngine.GPT4_TURBO,
        "GetMostSimilarCitations": ModelEngine.GPT4_TURBO,
        "IsGoalOK": ModelEngine.GPT4_TURBO,
        "TablesReviewBackgroundProductsConverser": ModelEngine.GPT4_TURBO,
        "IntroductionSectionWriterReviewGPT": ModelEngine.GPT4_TURBO,
        "DiscussionSectionWriterReviewGPT": ModelEngine.GPT4_TURBO,
    },
    "open": {
        "Converser": ModelEngine.LLAMA_2,
        "DataExplorationCodeProductsGPT": ModelEngine.CODELLAMA,
        "DataAnalysisCodeProductsGPT": ModelEngine.CODELLAMA,
        "CreateTablesCodeProductsGPT": ModelEngine.CODELLAMA,
        "GetMostSimilarCitations": ModelEngine.LLAMA_2,
        "IsGoalOK": ModelEngine.LLAMA_2,
        "TablesReviewBackgroundProductsConverser": ModelEngine.LLAMA_2,
        "IntroductionSectionWriterReviewGPT": ModelEngine.LLAMA_2,
        "DiscussionSectionWriterReviewGPT": ModelEngine.LLAMA_2,
    },
}
