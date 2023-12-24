import glob
import os, re

from pathlib import Path
from typing import Union
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
        'AdvanceStage(',
        'SetActiveConversation(',
        'SetProduct(',
        'SendFinalProduct('
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


def convert_console_log_to_html(output_directory: Union[str, Path]):
    """
    Convert the console log to a html file.
    """
    os.chdir(output_directory)
    file = glob.glob('console_log.txt')[0]
    # check if file exists and is not empty
    if os.path.isfile(file) and os.path.getsize(file) > 0:
        with open(file, 'r') as f:
            text_as_string = f.read()
            filtered_text = filter_text(text_as_string)
            text_as_string_html = convert_ansi_to_html(filtered_text)
            html_file = file.replace('.txt', '.html')
            with open(html_file, 'w') as new_f:
                new_f.write(text_as_string_html)
        return html_file
    else:
        raise FileNotFoundError(f'File {file} does not exist or is empty')
