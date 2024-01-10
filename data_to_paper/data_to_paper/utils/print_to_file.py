from typing import Optional

import colorama
from functools import partial

from .highlighted_text import colored_text
from .mutable import Mutable

CONSOLE_LOG_FILE = Mutable(None)


def print_and_log(text_in_bw: str, text_in_color: Optional[str] = None, color: Optional[str] = None,
                  should_log: bool = True, **kwargs):
    if color is not None:
        assert text_in_color is None
        text_in_color = colored_text(text_in_bw, color)
    else:
        if text_in_color is None:
            text_in_color = text_in_bw
    print(text_in_color, **kwargs)
    should_log = True  # for consistency with old outputs
    if should_log and CONSOLE_LOG_FILE.val is not None:
        file_path_color = CONSOLE_LOG_FILE.val  # pathlib.Path
        with open(file_path_color, 'a') as f:
            print(text_in_color, file=f, **kwargs)
        file_path_bw = file_path_color.with_stem(file_path_color.stem + '_bw')
        with open(file_path_bw, 'a') as f:
            print(text_in_bw, file=f, **kwargs)


print_and_log_red = partial(print_and_log, color=colorama.Fore.RED)
print_and_log_magenta = partial(print_and_log, color=colorama.Fore.MAGENTA)
