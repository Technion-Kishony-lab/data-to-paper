import colorama

from data_to_paper.terminate.exceptions import TerminateException


def resource_checking(title: str):
    def _resource_checking(func):

        def wrapper(*args, **kwargs):
            from data_to_paper.text.highlighted_text import colored_text, format_text_with_code_blocks
            from data_to_paper.utils.print_to_file import IS_LOGGING_ENABLED
            print(f"\n*** {title}\nRunning...")
            try:
                with IS_LOGGING_ENABLED.temporary_set(False):
                    func(*args, **kwargs)
            except Exception as e:
                color = colorama.Fore.CYAN if isinstance(e, TerminateException) else colorama.Fore.RED
                print(colored_text(f"Test failed:", color=colorama.Fore.RED))
                print(format_text_with_code_blocks(str(e), text_color=color))
            else:
                print(colored_text("Test successful!", color=colorama.Fore.GREEN))

        return wrapper
    return _resource_checking
