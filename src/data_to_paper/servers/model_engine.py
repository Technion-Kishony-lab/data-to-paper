from __future__ import annotations
from dataclasses import dataclass, fields
from typing import List, Tuple, Dict, TYPE_CHECKING

from data_to_paper.utils.types import IndexOrderedEnum

if TYPE_CHECKING:
    from data_to_paper.servers.types import APIKey


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
    LLAMA_2_7b = "Llama-2-7b-chat-hf"
    LLAMA_2_70b = "Llama-2-70b-chat-hf"
    CODELLAMA = "CodeLlama-34b-Instruct-hf"

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.value)

    def get_model_with_more_strength(self):
        model = MODELS_TO_MORE_STRENGTH.get(self)
        if model is None:
            raise ValueError(f"Model {self} has no stronger model")
        return model

    def get_model_with_more_context(self):
        model = MODELS_TO_MORE_CONTEXT.get(self)
        if model is None:
            raise ValueError(f"Model {self} has no model with more context")
        return model

    @property
    def max_tokens(self):
        return MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR[self][0]

    @property
    def pricing(self) -> Tuple[float, float]:
        """
        Return the pricing for the model engine.
        (dollar_per_in_token, dollar_per_out_token)
        """
        return MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR[self][1:]

    @property
    def allows_json_mode(self):
        return self in MODEL_ENGINES_ALLOWING_JSON_MODE

    @property
    def api_key(self) -> APIKey:
        return _get_api_key_and_server_name_and_base_url(self)[0]

    @property
    def base_url(self):
        return _get_api_key_and_server_name_and_base_url(self)[1]

    @property
    def server_name(self):
        return _get_api_key_and_server_name_and_base_url(self)[2]


ModelEngine.DEFAULT = ModelEngine.GPT4o_MINI

MODELS_TO_MORE_CONTEXT: Dict[ModelEngine, ModelEngine] = {
    ModelEngine.GPT35_TURBO: ModelEngine.GPT4_TURBO,
    ModelEngine.GPT4: ModelEngine.GPT4_TURBO,
    ModelEngine.GPT4_TURBO: ModelEngine.GPT4o,
    ModelEngine.GPT4o_MINI: ModelEngine.GPT4o,  # same as GPT4o
    ModelEngine.GPT4o: ModelEngine.GPT4o,  # same as GPT4o
}

MODELS_TO_MORE_STRENGTH: Dict[ModelEngine, ModelEngine] = {
    ModelEngine.GPT35_TURBO: ModelEngine.GPT4o,
    ModelEngine.GPT4: ModelEngine.GPT4o,
    ModelEngine.GPT4_TURBO: ModelEngine.GPT4o,
    ModelEngine.GPT4o_MINI: ModelEngine.GPT4o,
}

MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR: Dict[ModelEngine, Tuple[int, float, float]] = {
    ModelEngine.GPT35_TURBO: (16384, 0.000001, 0.000002),
    ModelEngine.GPT4: (8192, 0.00003, 0.00006),
    ModelEngine.GPT4_TURBO: (128000, 0.00001, 0.00003),
    ModelEngine.GPT4o_MINI: (128000, 1.5e-7, 6e-7),
    ModelEngine.GPT4o: (128000, 0.000005, 0.000015),
    ModelEngine.LLAMA_2_7b: (4096, 0.0002, 0.0002),
    ModelEngine.LLAMA_2_70b: (4096, 0.0007, 0.001),
    ModelEngine.CODELLAMA: (4096, 0.0006, 0.0006),
}

MODEL_ENGINES_ALLOWING_JSON_MODE = {ModelEngine.GPT4o_MINI, ModelEngine.GPT4o}

OPENAI_API_BASE = "https://api.openai.com/v1"
DEEPINFRA_API_BASE = "https://api.deepinfra.com/v1/openai"


def _get_api_key_and_server_name_and_base_url(model_engine: ModelEngine) -> Tuple[APIKey, str, str]:
    from data_to_paper.env import OPENAI_API_KEY, DEEPINFRA_API_KEY
    open_ai_key_and_base_url = (OPENAI_API_KEY, OPENAI_API_BASE, "OpenAI")
    deep_infra_key_and_base_url = (DEEPINFRA_API_KEY, DEEPINFRA_API_BASE, "DeepInfra")

    llm_models_to_api_keys_and_base_url: Dict[ModelEngine, Tuple[APIKey, str, str]] = {
        ModelEngine.GPT35_TURBO: open_ai_key_and_base_url,
        ModelEngine.GPT4: open_ai_key_and_base_url,
        ModelEngine.GPT4_TURBO: open_ai_key_and_base_url,
        ModelEngine.GPT4o_MINI: open_ai_key_and_base_url,
        ModelEngine.GPT4o: open_ai_key_and_base_url,
        ModelEngine.LLAMA_2_7b: deep_infra_key_and_base_url,
        ModelEngine.LLAMA_2_70b: deep_infra_key_and_base_url,
        ModelEngine.CODELLAMA: deep_infra_key_and_base_url,
    }
    return llm_models_to_api_keys_and_base_url[model_engine]


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
