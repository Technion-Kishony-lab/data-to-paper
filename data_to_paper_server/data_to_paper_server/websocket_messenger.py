from dataclasses import dataclass
from multiprocessing import Queue

from data_to_paper.base_cast.messenger import Messenger
from data_to_paper.conversation import Action
from data_to_paper_server.serializers import serialize_action


@dataclass
class QueueMessenger(Messenger):

    # TODO: shouldn't have a default
    writer: Queue = None

    def _update_on_action(self, action: Action):
        serialized = serialize_action(action)
        self.writer.put(serialized)
