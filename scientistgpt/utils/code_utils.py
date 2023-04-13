PYTHON_KEYWORD = 'import'


def is_code_in_response(response: str) -> bool:
    sections = response.split('```')
    return len(sections) > 1 and PYTHON_KEYWORD in sections[1]
