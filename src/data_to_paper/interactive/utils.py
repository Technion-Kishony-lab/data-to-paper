import os
import sys


def open_file_on_os(file_path):
    """
    Open a file with the default application.
    """
    if sys.platform == 'win32':
        os.startfile(file_path)
    else:
        # For macOS and Linux, we use 'open' and 'xdg-open' respectively
        opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
        os.system(f'{opener} "{file_path}"')
