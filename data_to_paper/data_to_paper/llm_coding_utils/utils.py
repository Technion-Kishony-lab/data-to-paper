from pathlib import Path


def convert_to_latex_comment(text: str) -> str:
    """
    Convert a string to a comment in latex.
    """
    lines = text.split('\n')
    return '% ' + '\n% '.join(lines)


def convert_filename_to_label(filename, label) -> str:
    """
    Convert a filename to a label.
    """
    if label:
        raise ValueError(f'Do not provide the `label` argument. The label is derived from the filename.')
    if not filename:
        return ''
    label = Path(filename).stem
    ext = Path(filename).suffix
    if ext:
        raise ValueError(f'Invalid filename: "{filename}". The filename must not have an extension.')

    # check if the label is valid:
    if not label.isidentifier():
        raise ValueError(f'Invalid filename: "{filename}". The filename must be a valid identifier.')
    label = label.replace('_', '-')
    return label
