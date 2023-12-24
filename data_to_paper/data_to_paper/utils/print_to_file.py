from typing import Optional

import colorama
from functools import partial

from .highlighted_text import colored_text
from .mutable import Mutable

CONSOLE_LOG_FILE = Mutable(None)


def print_and_log(*args, color: Optional[str] = None, should_log: bool = True, **kwargs):
    if color is not None:
        args = [colored_text(arg, color) for arg in args]
    print(*args, **kwargs)
    if should_log and CONSOLE_LOG_FILE.val is not None:
        with open(CONSOLE_LOG_FILE.val, 'a') as f:
            print(*args, **kwargs, file=f)


print_and_log_red = partial(print_and_log, color=colorama.Fore.RED)
print_and_log_magenta = partial(print_and_log, color=colorama.Fore.MAGENTA)
