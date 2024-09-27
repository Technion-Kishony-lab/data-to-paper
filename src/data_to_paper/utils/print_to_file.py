from contextlib import contextmanager
from typing import Optional

import colorama
from functools import partial

from pathlib import Path

from .console_log_to_html import convert_console_log_to_html
from data_to_paper.text.highlighted_text import colored_text
from .mutable import Mutable, Flag

CONSOLE_LOG_FILE = Mutable(None)

IS_LOGGING_ENABLED = Flag(True)


@contextmanager
def console_log_file_context(file_path: Path):
    """
    Context manager to temporarily change the console log file.
    If run is successful, also converts the console log to html.
    """
    global CONSOLE_LOG_FILE
    old_val = CONSOLE_LOG_FILE.val
    CONSOLE_LOG_FILE.val = file_path
    try:
        yield
    except Exception:
        raise
    else:
        convert_console_log_to_html(CONSOLE_LOG_FILE.val)
    finally:
        CONSOLE_LOG_FILE.val = old_val


def print_and_log(text_in_bw: str, text_in_color: Optional[str] = None, color: Optional[str] = None,
                  should_log: bool = True, **kwargs):
    if not IS_LOGGING_ENABLED:
        return
    if color is not None:
        assert text_in_color is None
        text_in_color = colored_text(text_in_bw, color)
    else:
        if text_in_color is None:
            text_in_color = text_in_bw
    print(text_in_color, **kwargs)
    if should_log and CONSOLE_LOG_FILE.val is not None:
        file_path_color = CONSOLE_LOG_FILE.val  # pathlib.Path
        with open(file_path_color, 'a', encoding='utf-8') as f:
            print(text_in_color, file=f, **kwargs)
        file_path_bw = file_path_color.with_stem(file_path_color.stem + '_bw')
        with open(file_path_bw, 'a', encoding='utf-8') as f:
            print(text_in_bw, file=f, **kwargs)


print_and_log_red = partial(print_and_log, color=colorama.Fore.RED)
print_and_log_magenta = partial(print_and_log, color=colorama.Fore.MAGENTA)
