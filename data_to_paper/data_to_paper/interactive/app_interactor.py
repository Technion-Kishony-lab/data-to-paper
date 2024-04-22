from dataclasses import dataclass, field
from typing import Optional, Dict, Union, Iterable

from data_to_paper.utils import format_text_with_code_blocks
from data_to_paper.utils.replacer import format_value
from data_to_paper.conversation.stage import Stage

from data_to_paper.servers.llm_call import get_human_response

from .base_app import BaseApp
from .get_app import get_or_create_app
from .types import PanelNames
from .human_actions import HumanAction, ButtonClickedHumanAction, TextSentHumanAction


@dataclass
class AppInteractor:

    app: Optional[BaseApp] = field(default_factory=get_or_create_app)

    def _app_clear_panels(self, panel_name: Union[PanelNames, Iterable[PanelNames]] = PanelNames):
        if self.app is None:
            return
        panel_names = panel_name if isinstance(panel_name, Iterable) else [panel_name]
        for panel_name in panel_names:
            self.app.show_text(panel_name, '')

    def _app_send_prompt(self, panel_name: PanelNames, prompt: str = '', provided_as_html: bool = False,
                         from_md: bool = False):
        if self.app is None:
            return
        s = format_value(self, prompt)
        if not provided_as_html:
            s = format_text_with_code_blocks(s, is_html=True, width=None, from_md=from_md)
        self.app.show_text(panel_name, s, is_html=True)

    def _app_request_continue(self):
        if self.app is None:
            return
        # self.app.request_continue()

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

    def _app_advance_stage(self, stage: Stage):
        if self.app is None:
            return
        self.app.advance_stage(stage)

    def _app_send_product_of_stage(self, stage: Stage, product_text: str):
        if self.app is None:
            return
        self.app.send_product_of_stage(stage, product_text)

    def _app_set_status(self, panel_name: PanelNames, status: str = ''):
        if self.app is None:
            return
        self.app.set_status(panel_name, 1, status)

    def _app_set_header(self, panel_name: PanelNames, header: str):
        if self.app is None:
            return
        self.app.set_status(panel_name, 0, header)
