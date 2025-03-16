from __future__ import annotations
from dataclasses import dataclass, fields
from typing import List, Tuple, Dict

import litellm


class ModelEngine:
    """
    Manages the current model engine.
    """

    def __init__(self, model_engine: str):
        self.value = model_engine

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def __hash__(self):
        return hash(self.value)

    def get_model_with_more_strength(self):
        model = MODELS_TO_MORE_STRENGTH.get(self.value)
        if model is None:
            raise ValueError(f"Model {self.value} has no stronger model")
        return ModelEngine(model)

    def get_model_with_more_context(self):
        model = MODELS_TO_MORE_CONTEXT.get(self.value)
        if model is None:
            raise ValueError(f"Model {self.value} has no model with more context")
        return ModelEngine(model)

    @property
    def max_tokens(self):
        return litellm.get_max_tokens(self.value)

    @property
    def pricing(self) -> Tuple[float, float]:
        """
        Return the pricing for the model engine.
        (dollar_per_in_token, dollar_per_out_token)
        """
        model_info = litellm.get_model_info(self.value)
        return model_info["input_cost_per_token"], model_info["output_cost_per_token"]

    @property
    def allows_json_mode(self):
        return litellm.supports_response_schema(model=self.value)

    @property
    def api_key(self) -> str:
        return _get_api_key_and_server_name_and_base_url(self)[0]

    @property
    def base_url(self) -> str:
        return _get_api_key_and_server_name_and_base_url(self)[1]

    @property
    def server_name(self) -> str:
        return _get_api_key_and_server_name_and_base_url(self)[2]


MODELS_TO_MORE_CONTEXT: Dict[ModelEngine, ModelEngine] = {
    "gpt-4": "gpt-4o",
    "gpt-4-turbo": "gpt-4o",
    "gpt-4-mini": "gpt-4o",
    "gpt-4o": "o1",
    "o1-mini": "o1",
    "o1": "o3-mini",
}

MODELS_TO_MORE_STRENGTH: Dict[ModelEngine, ModelEngine] = {
    "gpt-4": "gpt-4o",
    "gpt-4-turbo": "gpt-4o",
    "gpt-4-mini": "gpt-4o",
    "gpt-4o": "o1",
    "o1-mini": "o1",
    "o1": "o3-mini",
}


def _get_api_key_and_server_name_and_base_url(
    model_engine: str,
) -> Tuple[str, str, str]:
    model, custom_llm_provider, dynamic_api_key, api_base = litellm.get_llm_provider(
        model=model_engine.value
    )
    return dynamic_api_key, api_base, custom_llm_provider


@dataclass
class LLMCallParameters:
    """
    Parameters for calling LLM API.
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


LLM_CALL_PARAMETERS_NAMES = [field.name for field in fields(LLMCallParameters)]
