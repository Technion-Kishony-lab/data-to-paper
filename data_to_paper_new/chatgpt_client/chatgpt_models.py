from enum import Enum


class ModelEngine(Enum):
    """
    Enum for the different model engines available in openai.
    Support comparison operators, according to the order of the enum.
    """
    GPT35_TURBO = "gpt-3.5-turbo-0613"  # latest version that supports better system prompt adherence
    GPT35_TURBO_16 = "gpt-3.5-turbo-16k-0613"
    GPT4 = "gpt-4-0613"
    # GPT4_32 = "gpt-4-32k"

class ChatGptRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
