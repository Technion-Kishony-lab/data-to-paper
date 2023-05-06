from scientistgpt.scientistgpt import replay_actions
from local_paths import OUTPUT_FOLDER
from pathlib import Path

filename = Path(OUTPUT_FOLDER) / 'conversation_actions'

replay_actions(filename)
