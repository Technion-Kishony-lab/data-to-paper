from dataclasses import dataclass
from typing import Optional, Dict, Union, Iterable

from data_to_paper.utils import format_text_with_code_blocks
from data_to_paper.utils.replacer import format_value

from data_to_paper.servers.llm_call import get_human_response

from . import the_app
from .base_app import BaseApp
from .types import PanelNames
from .human_actions import HumanAction, ButtonClickedHumanAction, TextSentHumanAction


@dataclass
class AppInteractor:

    app: Optional[BaseApp] = the_app

    def _app_clear_panels(self, panel_name: Union[PanelNames, Iterable[PanelNames]] = PanelNames):
        if self.app is None:
            return
        panel_names = panel_name if isinstance(panel_name, Iterable) else [panel_name]
        for panel_name in panel_names:
            self.app.show_text(panel_name, '')

    def _app_send_prompt(self, panel_name: PanelNames, prompt: str, provided_as_html: bool = False,
                         from_md: bool = False):
        if self.app is None:
            return
        s = format_value(self, prompt or '')
        if not provided_as_html:
            s = format_text_with_code_blocks(s, is_html=True, width=None, from_md=from_md)
        self.app.show_text(panel_name, s, is_html=True)

    def _app_request_continue(self):
        if self.app is None:
            return
        self.app.request_continue()

    def _app_set_focus_on_panel(self, panel_name: PanelNames):
        if self.app is None:
            return
        self.app.set_focus_on_panel(panel_name)

    def _app_receive_text(self, panel_name: PanelNames, initial_text: str = '',
                          title: Optional[str] = None,
                          optional_suggestions: Dict[str, str] = None) -> str:
        action = self._app_receive_action(panel_name, initial_text, title, optional_suggestions)
        if isinstance(action, TextSentHumanAction):
            return action.value
        button = action.value
        if button == 'Initial':
            return initial_text
        return optional_suggestions[button]

    def _app_receive_action(self, panel_name: PanelNames, initial_text: str = '',
                            title: Optional[str] = None,
                            optional_suggestions: Dict[str, str] = None) -> HumanAction:
        if self.app is None:
            return ButtonClickedHumanAction('Initial')
        return get_human_response(self.app,
                                  panel_name=panel_name,
                                  initial_text=initial_text,
                                  title=title,
                                  optional_suggestions=optional_suggestions)
