TRANSLATION_TABLE = {
    "you are": "I am",
    "you have": "I have",
    "you will": "I will",
    "you should": "I should",
    "you're": "I'm",
    "you've": "I've",
    "to you": "to me",
    "your": "my",
    "yours": "mine",
    "you": "I",
    "yourself": "myself",
}


def translate_second_person_to_first_person(text: str) -> str:
    """
    Translate a second person text to a first person text.
    """

    for k, v in TRANSLATION_TABLE.items():
        text = text.replace(k, v)
        text = text.replace(k.capitalize(), v.capitalize())

    return text
