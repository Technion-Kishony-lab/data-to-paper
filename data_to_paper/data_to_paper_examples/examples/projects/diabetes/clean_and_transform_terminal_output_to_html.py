import glob, os, re
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


os.chdir("./outputs")
text_files = glob.glob("*terminal_output.txt")

for file in text_files:
    with open(file, 'r') as f:
        text_as_string = f.read()
        filtered_text = filter_text(text_as_string)
        text_as_string_html = convert_ansi_to_html(filtered_text)
        with open(file[:-4] + '.html', 'w') as rf:
            rf.write(text_as_string_html)
        # if file.startswith('paper2') and '10' not in file:
        #     with open('runB' + file[7:-4] + '.html', 'w') as rf:
        #         rf.write(text_as_string_html)
        # elif file.startswith('paper2') and '10' in file:
        #     with open('runB' + file[6:-4] + '.html', 'w') as rf:
        #         rf.write(text_as_string_html)
        # else:
        #     with open('runA' + file[8:-4] + '.html', 'w') as rf:
        #         rf.write(text_as_string_html)
