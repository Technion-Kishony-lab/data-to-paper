import re
import textwrap

PYTHON_KEYWORD = 'import'

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


def is_code_in_response(response: str) -> bool:
    sections = response.split('```')
    return len(sections) > 1 and PYTHON_KEYWORD in sections[1]


def wrap_text_with_triple_quotes(text: str, header: str = '') -> str:
    """
    Wrap text with triple quotes.
    """
    return f'```{header}\n{text}\n```'


def wrap_python_code(code, width=70):
    wrapped_lines = []
    for line in code.splitlines():
        stripped_line = line.strip()
        # Wrap comments
        if stripped_line.startswith("#"):
            # Preserve the leading whitespace
            leading_whitespace = line[:line.index("#")]
            wrapped_comment = textwrap.fill(stripped_line, width=width,
                                            initial_indent=leading_whitespace,
                                            subsequent_indent=leading_whitespace + "# ",
                                            break_long_words=False,
                                            break_on_hyphens=False)
            wrapped_lines.extend(wrapped_comment.splitlines())
        # Wrap non-empty lines that are not comments
        elif stripped_line:
            wrapped_line = textwrap.wrap(line, width=width,
                                         break_long_words=False,
                                         break_on_hyphens=False)
            for i, part in enumerate(wrapped_line[:-1]):
                wrapped_lines.append(part + " \\")
            # Align the continuation lines with the original line's indentation
            continuation_indent = len(line) - len(line.lstrip())
            wrapped_lines.append(" " * continuation_indent + wrapped_line[-1])
        else:
            wrapped_lines.append(line)
    return "\n".join(wrapped_lines)
