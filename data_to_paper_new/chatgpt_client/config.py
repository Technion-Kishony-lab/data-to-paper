from typing import Optional

from data_to_paper_new.chatgpt_client.chatgpt_models import ModelEngine

MODEL_ENGINE_TO_MAX_TOKENS_AND_IN_OUT_DOLLAR = {
    "gpt-3.5-turbo-0613": (4096, 0.0015, 0.002),
    "gpt-3.5-turbo-16k-0613": (16384, 0.003, 0.004),
    "gpt-4-0613": (8192, 0.03, 0.06),
    # "gpt-4-32k": 32768,
}


OPENAI_MODELS_TO_API_KEYS = dict[ModelEngine]({
    ModelEngine.GPT35_TURBO: "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",
    ModelEngine.GPT4: "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"
})

# Why with org?
OPENAI_MODELS_TO_ORGANIZATIONS_AND_API_KEYS = dict[Optional[ModelEngine], str]({
    ModelEngine.GPT35_TURBO:
        ("org-gvr0szNH28eeeuMCEG9JrwcR",
         "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"),
    ModelEngine.GPT4:
        ("org-SplsVAouKqk9mWIpVgIIVwSD",
         "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"),
})