from typing import Dict, Optional, Union, Type

import colorama

from data_to_paper.utils.print_to_file import print_and_log
from data_to_paper.conversation.stage import Stage

from .enum_types import PanelNames
from .human_actions import ButtonClickedHumanAction, TextSentHumanAction, HumanAction, RequestInfoHumanAction

REQUESTING_MISSING_TEXT = "Requesting..."


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
        self.step_runner = None
        self.stage_to_reset_to = None
        self._panels_and_positions_to_headers = {(panel_name, position): '' for panel_name in PanelNames
                                                 for position in range(2)}

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance

    def request_panel_continue(self, panel_name: PanelNames):
        pass

    def request_text(self, panel_name: PanelNames, initial_text: str = '',
                     title: Optional[str] = None,
                     instructions: Optional[str] = None,
                     optional_suggestions: Dict[str, str] = None) -> str:
        return initial_text

    def request_action(self, panel_name: PanelNames, initial_text: str = '',
                       title: Optional[str] = None,
                       instructions: Optional[str] = None,
                       in_field_instructions: Optional[str] = '',
                       optional_suggestions: Dict[str, str] = None) -> HumanAction:
        """
        Requests text from the user.
        User can choose to edit the text, or select one of the optional suggestions.
        """
        optional_suggestions = optional_suggestions or {}
        optional_suggestions = {"Initial": initial_text, **optional_suggestions}
        text = self.request_text(panel_name, initial_text, title, instructions, in_field_instructions,
                                 optional_suggestions)
        if text == REQUESTING_MISSING_TEXT:
            return RequestInfoHumanAction('AI')
        if text == initial_text:
            return ButtonClickedHumanAction('Initial')
        for suggestion_name, suggestion_content in optional_suggestions.items():
            if text == suggestion_content:
                return ButtonClickedHumanAction(suggestion_name)
        return TextSentHumanAction(text)

    def request_reset_to_step(self, step_name: str):
        pass

    def show_text(self, panel_name: PanelNames, text: str, is_html: bool = False,
                  scroll_to_bottom: bool = False):
        pass

    def set_focus_on_panel(self, panel_name: PanelNames):
        pass

    def advance_stage(self, stage: Union[Stage, int, bool]):
        """
        Advances the stage.
        stage:
            Stage: the stage to advance to.
            int: the index of the stage to advance to.
            True: advance to the end (all stages are completed).
            False: advance to the beginning (before the first stage).
        """
        pass

    def send_product_of_stage(self, stage: Stage, product_text: str):
        pass

    def initialize(self):
        pass

    def _run_all_steps(self):
        self.step_runner.run_all_steps()

    def _get_stages(self) -> Type[Stage]:
        if self.step_runner is None:
            return Stage
        return self.step_runner.stages

    def _set_status(self, panel_name: PanelNames, position: int, status: str = ''):
        pass

    def clear_stage_to_reset_to(self):
        self.stage_to_reset_to = None

    def set_status(self, panel_name: PanelNames, position: int, status: str = ''):
        self._panels_and_positions_to_headers[(panel_name, position)] = status
        self._set_status(panel_name, position, status)

    def get_status(self, panel_name: PanelNames, position: int) -> str:
        return self._panels_and_positions_to_headers[(panel_name, position)]

    def set_header(self, header: str):
        pass

    def send_api_usage_cost(self, stages_to_costs: Dict[Stage, float]):
        pass


class ConsoleApp(BaseApp):
    """
    A console-based application.
    Very simple implementation of the edit_text and show_text methods, for debugging purposes.
    """

    def initialize(self):
        self._run_all_steps()

    @staticmethod
    def get_multiline_input() -> str:
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        return '\n'.join(lines)

    def request_text(self, panel_name: PanelNames, initial_text: str = '',
                     title: Optional[str] = None,
                     instructions: Optional[str] = None,
                     optional_suggestions: Dict[str, str] = None) -> str:
        if panel_name != PanelNames.FEEDBACK:
            # In the console app, we only support the feedback panel:
            return initial_text
        color = colorama.Fore.BLUE
        light_color = colorama.Fore.LIGHTBLUE_EX
        print_and_log(title, color=light_color)
        print_and_log("Suggestions:", should_log=False, color=color)
        print_and_log(f"#{0}. {'Initial content'}:", should_log=False, color=light_color)
        print_and_log(initial_text or "<empty>", should_log=False, color=color)
        if optional_suggestions:
            for index, (suggestion_name, suggestion_content) in enumerate(optional_suggestions.items()):
                print_and_log(f"#{index + 1}. {suggestion_name}:", should_log=False, color=light_color)
                print_and_log(suggestion_content or "<empty>", should_log=False, color=color)
        print_and_log("Enter your text, or the number of the suggestion you want to use "
                      f"(0 - {len(optional_suggestions)}): (use Enter newline. End with an empty line to submit)",
                      should_log=False, color=color)
        text = self.get_multiline_input().strip()
        if text.isdigit():
            suggestion_index = int(text)
            if suggestion_index == 0:
                text = initial_text
            else:
                text = list(optional_suggestions.values())[suggestion_index - 1]
        print_and_log(f"Text received:", color=light_color)
        print_and_log(text or "<empty>", color=color)
        return text

    def show_text(self, panel_name: PanelNames, text: str, is_html: bool = False,
                  scroll_to_bottom: bool = False):
        # print_and_log(text)
        pass  # no need to print, user already sees all console messages.
