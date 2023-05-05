from g3pt.utils.ordered_enum import IndexOrderedEnum


class ModelEngine(IndexOrderedEnum):
    """
    Enum for the different model engines available in openai.
    Support comparison operators, according to the order of the enum.
    """
    GPT35_TURBO = "gpt-3.5-turbo"
    GPT4 = "gpt-4"
    GPT4_32 = "gpt-4-32k"
