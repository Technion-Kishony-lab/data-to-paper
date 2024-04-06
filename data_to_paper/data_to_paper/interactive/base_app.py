from typing import Dict, Optional

from data_to_paper.utils.print_to_file import print_and_log

from .types import PanelNames
from .human_actions import ButtonClickedHumanAction, TextSentHumanAction, HumanAction


class BaseApp:
    """
    A base class for the application.
    Provides the main interface for the application, including:
    - show_text
    - edit_text
    """

    # make sure the app is singleton
    instance = None

    def __init__(self):
        # make sure the app is singleton
        if self.instance is not None:
            raise Exception("App is a singleton!")
        self.instance = self

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance

    def _request_text(self, panel_name: PanelNames, initial_text: str = '',
                      title: Optional[str] = None, optional_suggestions: Dict[str, str] = None) -> str:
        pass

    def request_text(self, panel_name: PanelNames, initial_text: str = '',
                     title: Optional[str] = None, optional_suggestions: Dict[str, str] = None) -> HumanAction:
        """
        Requests text from the user.
        User can choose to edit the text, or select one of the optional suggestions.
        """
        text = self._request_text(panel_name, initial_text, title, optional_suggestions)
        if text == initial_text:
            return ButtonClickedHumanAction('Initial')
        for suggestion_name, suggestion_content in optional_suggestions.items():
            if text == suggestion_content:
                return ButtonClickedHumanAction(suggestion_name)
        return TextSentHumanAction(text)

    def show_text(self, panel_name: PanelNames, text: str, is_html: bool = False):
        pass


class ConsoleApp(BaseApp):
    """
    A console-based application.
    Very simple implementation of the edit_text and show_text methods, for debugging purposes.
    """

    @staticmethod
    def get_multiline_input() -> str:
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        return '\n'.join(lines)

    def initialize(self):
        pass

    def request_text(self, panel_name: PanelNames, initial_text: str = '',
                     title: Optional[str] = None, optional_suggestions: Dict[str, str] = None) -> str:
        print_and_log(title)
        print_and_log("Suggestions:")
        print_and_log(f"{0}. {'Initial content'}")
        print_and_log(initial_text)
        if optional_suggestions:
            for index, (suggestion_name, suggestion_content) in enumerate(optional_suggestions.items()):
                print_and_log(f"{index + 1}. {suggestion_name}")
                print_and_log(suggestion_content)
        print_and_log("Enter your text, or the number of the suggestion you want to use:")
        text = self.get_multiline_input()
        if text.isdigit():
            suggestion_index = int(text)
            if suggestion_index == 0:
                return initial_text
            return list(optional_suggestions.values())[suggestion_index - 1]

    def show_text(self, panel_name: PanelNames, text: str, is_html: bool = False):
        print_and_log(text)
