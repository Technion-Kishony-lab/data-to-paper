import os
import re

from pathlib import Path
from ansi2html import Ansi2HTMLConverter


def convert_ansi_to_html(ansi_text):
    conv = Ansi2HTMLConverter()
    html_text = conv.convert(ansi_text, full=True)
    return html_text


def filter_text(text):
    lines = text.split('\n')
    lines_to_filter_startswith = [
        ' [31mERROR: None embedding attr.',
        ' [31mCreateConversation(',
    ]
    # Filter out lines based on the startswith conditions
    filtered_lines = [
        line for line in lines
        if not any(line.startswith(prefix) for prefix in lines_to_filter_startswith)
    ]
    # Remove everything from "This is BibTeX," to the end of the document
    for i, line in enumerate(filtered_lines):
        if line.startswith("This is BibTeX,"):
            filtered_lines = filtered_lines[:i]
            break
    # Join the lines into a single string
    filtered_text = '\n'.join(filtered_lines)
    # Replace three or more consecutive newline characters with two newline characters
    filtered_text = re.sub(r'\n{3,}', '\n', filtered_text)
    return filtered_text


def convert_console_log_to_html(console_filepath: Path):
    """
    Convert the console log to a html file.
    """
    # check if file exists and is not empty
    if not os.path.isfile(console_filepath) or not os.path.getsize(console_filepath) > 0:
        raise FileNotFoundError(f'File {console_filepath} does not exist or is empty')
    with open(console_filepath, 'r', encoding='utf-8') as f:
        text_as_string = f.read()
        filtered_text = filter_text(text_as_string)
        text_as_string_html = convert_ansi_to_html(filtered_text)
        html_file = console_filepath.parent / (console_filepath.stem + '.html')
        with open(html_file, 'w', encoding='utf-8') as new_f:
            new_f.write(text_as_string_html)
    return html_file
