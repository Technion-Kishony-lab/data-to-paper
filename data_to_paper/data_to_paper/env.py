import os
from typing import Optional

from pathlib import Path

from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils.mutable import Mutable, Flag

BASE_FOLDER = Path(__file__).parent.parent.parent

SUPPORTED_PACKAGES = ('numpy', 'pandas', 'scipy', 'sklearn')

OPENAI_API_BASE = "https://api.openai.com/v1"
DEEPINFRA_API_BASE = "https://api.deepinfra.com/v1/openai"

# OpenAI API keys. model=None is the default key.
LLM_MODELS_TO_API_KEYS_AND_BASE_URL = dict[Optional[ModelEngine], str]({
    None:
        (os.environ.get('OPENAI_API_KEY'), OPENAI_API_BASE),
    ModelEngine.GPT4:
        (os.environ.get('OPENAI_API_KEY'), OPENAI_API_BASE),
    ModelEngine.GPT4_TURBO:
        (os.environ.get('OPENAI_API_KEY'), OPENAI_API_BASE),
    ModelEngine.LLAMA_2_7b:
        (os.environ.get('DEEPINFRA_API_KEY'), DEEPINFRA_API_BASE),
    ModelEngine.LLAMA_2_70b:
        (os.environ.get('DEEPINFRA_API_KEY'), DEEPINFRA_API_BASE),
    ModelEngine.CODELLAMA:
        (os.environ.get('DEEPINFRA_API_KEY'), DEEPINFRA_API_BASE),
})

SEMANTIC_SCHOLAR_API_KEY = os.environ.get('SEMANTIC_SCHOLAR_API_KEY', None)

DEFAULT_MODEL_ENGINE = ModelEngine.GPT35_TURBO

# Text width for conversation output:
TEXT_WIDTH = 150

# max time for code timeout when running LLM-writen code (seconds)
MAX_EXEC_TIME = Mutable(200)

# Decide whether to present code debugging iterations as code diff or full.
# Defining: compaction_code_diff = num_lines(new_code) - num_lines(code_diff)
# We show code diff if compaction_code_diff > MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF
MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF = Mutable(20)  # Use 0 to always show code diff, or None to always show full code

# Decide whether to show incomplete code in the output:
HIDE_INCOMPLETE_CODE = Flag(True)

# Max number of tokens allowed in code output:
MAX_SENSIBLE_OUTPUT_SIZE_TOKENS = Mutable(2500)

# Delay for cache retrieval (for replay to behave as if we are waiting for the server):
DELAY_CODE_RUN_CACHE_RETRIEVAL = Mutable(0.01)  # seconds
DELAY_SERVER_CACHE_RETRIEVAL = Mutable(0.01)  # seconds

# Pause time (in seconds). 0 for no pause; None to wait for Continue button.
PAUSE_AT_RULE_BASED_FEEDBACK = Mutable(None)
PAUSE_AT_LLM_FEEDBACK = Mutable(None)
PAUSE_AT_PROMPT_FOR_LLM_FEEDBACK = Mutable(None)
PAUSE_AFTER_LITERATURE_SEARCH = Mutable(None)
REQUEST_CONTINUE_IN_PLAYBACK = Flag(True)
FAKE_REQUEST_HUMAN_RESPONSE_ON_PLAYBACK = Flag(False)  # For video recording

# Human interactions:
# CHOSEN_APP:
#   'console': console-based interaction
#   'pyside': GUI-based interaction (requires installing PySide6)
#    None: Does not ask for or records human interactions (legacy. not recommended).
# Runs recorded with 'pyside'/'console' can be replayed with either 'pyside'/'console',
# but not with None. Runs recorded with None can be replayed only with None.
CHOSEN_APP = Mutable('pyside')

# Human code review:
# If True, the user can change all code reviews.
# If None, the user can change only the last code review.
# If False, the user cannot change code reviews.
HUMAN_EDIT_CODE_REVIEW = None

HUMAN_NAME = 'Human'

NUM_DIGITS_FOR_FLOATS = 4

FOLDER_FOR_RUN = Path(__file__).parent / 'temp_run'

# GPT code environment:
TRACK_P_VALUES = Flag(True)

# Debugging switches:
SHOW_LLM_CONTEXT = Flag(True)
SAVE_INTERMEDIATE_LATEX = Flag(False)
PRINT_CITATIONS = Flag(True)
PRINT_COMMENTS = Flag(False)
