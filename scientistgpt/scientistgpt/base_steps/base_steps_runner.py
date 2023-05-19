import glob
import os
from dataclasses import dataclass, field

from pathlib import Path
from typing import Union

from scientistgpt.env import COALESCE_WEB_CONVERSATIONS
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.servers.crossref import CROSSREF_SERVER_CALLER
from scientistgpt.conversation.conversation_actions import CreateConversation
from scientistgpt.conversation.stage import Stage, AdvanceStage, SetActiveConversation, SetProduct
from scientistgpt.conversation.conversation import WEB_CONVERSATION_NAME_PREFIX
from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations
from scientistgpt.base_cast import Agent

from .base_products_conversers import BaseProductsHandler
from .exceptions import FailedCreatingProductException
from .types import DataFileDescriptions


@dataclass
class BaseStepsRunner(BaseProductsHandler):
    """
    A base class for running a series of steps whose Products gradually accumulate towards a high level goal.
    """
    ACTIONS_FILENAME = 'conversation_actions.pkl'
    OPENAI_RESPONSES_FILENAME = 'openai_responses.txt'
    CROSSREF_RESPONSES_FILENAME = 'crossref_responses.txt'

    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)

    cast = None  # Type[Agent]
    data_file_descriptions: DataFileDescriptions = None
    mock_servers: Union[bool, str] = False

    def create_web_conversations(self):
        if not COALESCE_WEB_CONVERSATIONS:
            return
        if self.cast is None:
            return
        for agent in self.cast:
            if agent.get_conversation_name():
                self.actions_and_conversations.actions.apply_action(CreateConversation(
                    conversations=self.actions_and_conversations.conversations,
                    web_conversation_name=self.get_conversation_name_for_agent(agent),
                    participants={agent, self.cast.get_primary_agent()},
                ))

    def get_conversation_name_for_agent(self, agent):
        """
        Get the conversation name for the given agent.
        """
        if agent.get_conversation_name():
            return WEB_CONVERSATION_NAME_PREFIX + agent.get_conversation_name()
        return None

    def advance_stage(self, stage: Stage):
        """
        Advance the stage of the research goal.
        """
        self.actions_and_conversations.actions.apply_action(AdvanceStage(stage=stage))

    def set_active_conversation(self, agent: Agent):
        """
        Advance the stage of the research goal.
        """
        self.actions_and_conversations.actions.apply_action(SetActiveConversation(agent=agent))

    def advance_stage_and_set_active_conversation(self, stage: Stage = None, agent: Agent = None):
        """
        Advance the stage of the research goal.
        """
        if stage is not None:
            self.advance_stage(stage=stage)
        if agent is not None:
            self.set_active_conversation(agent=agent)

    def send_product_to_client(self, product_field: str):
        """
        Get the base GPT script file.
        """
        self.actions_and_conversations.actions.apply_action(
            SetProduct(
                stage=self.products.get_stage(product_field),
                products=self.products,
                product_field=product_field))

    @property
    def absolute_data_folder(self):
        return self.data_file_descriptions.data_folder

    def _run_all_steps(self):
        """
        Run all the steps towards the high level goal.
        """
        raise NotImplementedError

    def create_empty_output_folder(self):
        """
        Create empty output folder (delete all files if exists).
        """
        if os.path.exists(self.output_directory):
            # delete all the files except the mock_openai file:
            for file in glob.glob(str(self.output_directory / '*')):
                if file != str(self.output_directory / self.OPENAI_RESPONSES_FILENAME):
                    os.remove(file)
        else:
            os.makedirs(self.output_directory)

    def get_mock_responses_file(self, file_name: str = None):
        if self.mock_servers is False:
            return None
        directory = self.output_directory if self.mock_servers is True else self.mock_servers
        return Path(directory).absolute() / file_name

    @property
    def should_mock(self):
        return self.mock_servers is not False

    def run_all_steps(self):
        """
        Run all steps and save all created files to the output folder.
        """
        self.create_empty_output_folder()

        @OPENAI_SERVER_CALLER.record_or_replay(self.get_mock_responses_file(self.OPENAI_RESPONSES_FILENAME),
                                               should_mock=self.should_mock)
        @CROSSREF_SERVER_CALLER.record_or_replay(self.get_mock_responses_file(self.CROSSREF_RESPONSES_FILENAME),
                                                 should_mock=self.should_mock)
        def run():
            self.create_web_conversations()
            self._run_all_steps()

        try:
            run()
        except FailedCreatingProductException as e:
            self.advance_stage(Stage.FAILURE)
            print('----- FAILURE ------')
            print(f'Failed creating product: {e.product_field}')
        except Exception:
            raise
        else:
            self.advance_stage(Stage.FINISHED)
