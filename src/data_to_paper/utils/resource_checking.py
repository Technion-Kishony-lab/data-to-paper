import colorama


def resource_checking(title: str):
    def _resource_checking(func):
        def wrapper(*args, **kwargs):
            from data_to_paper.utils.highlighted_text import colored_text
            from data_to_paper.utils.print_to_file import IS_LOGGING_ENABLED
            print(f"\n*** {title}\nRunning...")
            try:
                with IS_LOGGING_ENABLED.temporary_set(False):
                    func(*args, **kwargs)
            except Exception as e:
                print(colored_text(f"Test failed:\n{e}", color=colorama.Fore.RED))
                return
            print(colored_text("Test successful!", color=colorama.Fore.GREEN))
        return wrapper
    return _resource_checking