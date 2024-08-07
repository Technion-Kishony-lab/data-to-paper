from dataclasses import dataclass, fields
from typing import List, Tuple

from data_to_paper.utils.types import IndexOrderedEnum


class ModelEngine(IndexOrderedEnum):
    """
    Enum for the different model engines available.
    Support comparison operators, according to the order of the enum.
    """

    # ignore:
    _ignore_ = ['DEFAULT']

    DEFAULT = None
    GPT35_TURBO = "gpt-3.5-turbo"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4o_MINI = "gpt-4o-mini"
    GPT4o = "gpt-4o"
    LLAMA_2_7b = "meta-llama/Llama-2-7b-chat-hf"
    LLAMA_2_70b = "meta-llama/Llama-2-70b-chat-hf"
    CODELLAMA = "codellama/CodeLlama-34b-Instruct-hf"

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.value)

    def get_model_with_more_strength(self):
        model = ModelEngine.MODELS_TO_MORE_STRENGTH.get(self)
        if model is None:
            raise ValueError(f"Model {self} has no stronger model")
        return model

    def get_model_with_more_context(self):
        model = ModelEngine.MODELS_TO_MORE_CONTEXT.get(self)
        if model is None:
            raise ValueError(f"Model {self} has no model with more context")
        return model

    @property
    def max_tokens(self):
        return ModelEngine.MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR[self][0]

    @property
    def pricing(self) -> Tuple[float, float]:
        """
        Return the pricing for the model engine.
        (in_dollar_per_token, out_dollar_per_token)
        """
        return ModelEngine.MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR[self][1:]


ModelEngine.DEFAULT = ModelEngine.GPT4o_MINI

ModelEngine.MODELS_TO_MORE_CONTEXT = dict()
ModelEngine.MODELS_TO_MORE_CONTEXT[ModelEngine.GPT35_TURBO] = ModelEngine.GPT4_TURBO
ModelEngine.MODELS_TO_MORE_CONTEXT[ModelEngine.GPT4]= ModelEngine.GPT4_TURBO

ModelEngine.MODELS_TO_MORE_STRENGTH = dict()
ModelEngine.MODELS_TO_MORE_STRENGTH[ModelEngine.GPT35_TURBO] = ModelEngine.GPT4o
ModelEngine.MODELS_TO_MORE_STRENGTH[ModelEngine.GPT4] = ModelEngine.GPT4o
ModelEngine.MODELS_TO_MORE_STRENGTH[ModelEngine.GPT4_TURBO] = ModelEngine.GPT4o
ModelEngine.MODELS_TO_MORE_STRENGTH[ModelEngine.GPT4o_MINI] = ModelEngine.GPT4o

ModelEngine.MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR = {
    ModelEngine.GPT35_TURBO: (16384, 0.000001, 0.000002),
    ModelEngine.GPT4: (8192, 0.00003, 0.00006),
    ModelEngine.GPT4_TURBO: (128000, 0.00001, 0.00003),
    ModelEngine.GPT4o_MINI: (128000, 1.5e-7, 6e-7),
    ModelEngine.GPT4o: (128000, 0.000005, 0.000015),
    ModelEngine.LLAMA_2_7b: (4096, 0.0002, 0.0002),
    ModelEngine.LLAMA_2_70b: (4096, 0.0007, 0.001),
    ModelEngine.CODELLAMA: (4096, 0.0006, 0.0006),
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


OPENAI_CALL_PARAMETERS_NAMES = [field.name for field in fields(OpenaiCallParameters)]
