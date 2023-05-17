import re

# different code formats that we have observed in chatgpt responses:
POSSIBLE_CODE_HEADERS = ["```python\n", "``` python\n", "```\n", "``` \n"]
CORRECT_CODE_HEADER = "```python\n"
CODE_REGEXP = f'{CORRECT_CODE_HEADER}(.*?)\n```'


def add_python_label_to_first_triple_quotes_if_missing(content: str):
    """
    Add "python" to triple quotes if missing.
    We assume the first triple quotes are the code block.
    """
    first_triple_quotes = content.find('```')

    if first_triple_quotes == -1:
        return content

    first_triple_quotes_end = content.find('\n', first_triple_quotes)
    if first_triple_quotes_end == -1:
        return content
    first_triple_quotes_line = content[first_triple_quotes:first_triple_quotes_end + 1]
    if first_triple_quotes_line in POSSIBLE_CODE_HEADERS:
        return content.replace(first_triple_quotes_line, CORRECT_CODE_HEADER, 1)
    return content


def remove_text_label_from_text_blocks(text: str) -> str:
    """
    Remove the label 'text', if any, from text blocks.
    """
    text = text.replace('```text\n', '```\n')
    text = text.replace('``` text\n', '```\n')
    return text


def extract_code_from_text(text: str) -> str:
    """
    Extract code from text.
    Assumes that text has a single code block.
    """
    corrected_content = add_python_label_to_first_triple_quotes_if_missing(text)
    return re.findall(CODE_REGEXP, corrected_content, re.DOTALL)[0].strip()
