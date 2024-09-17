from pathlib import Path

from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils.mutable import Mutable, Flag
from data_to_paper.servers.types import APIKey
from data_to_paper.types import HumanReviewType

BASE_FOLDER = Path(__file__).parent
FOLDER_FOR_RUN = Path(__file__).parent / 'temp_run'

""" API KEYS """
# Define API keys. See INSTALL.md for instructions.
OPENAI_API_KEY = APIKey.from_env('OPENAI_API_KEY')
DEEPINFRA_API_KEY = APIKey.from_env('DEEPINFRA_API_KEY')
SEMANTIC_SCHOLAR_API_KEY = APIKey.from_env('SEMANTIC_SCHOLAR_API_KEY')

""" LLM MODELS """
# Choose LLM model engines:
CODING_MODEL_ENGINE = ModelEngine.GPT4o
JSON_MODEL_ENGINE = ModelEngine.GPT4o
WRITING_MODEL_ENGINE = ModelEngine.GPT4o

# Use json mode when requesting LLM structured response:
JSON_MODE = True

""" LLM-CREATED CODE """
# Supported packages for LLM code:
SUPPORTED_PACKAGES = ('numpy', 'pandas', 'scipy', 'sklearn')

# max time for code timeout when running LLM-writen code (seconds)
MAX_EXEC_TIME = Mutable(600)

# Round numbers in LLM code output:
NUM_DIGITS_FOR_FLOATS = 4

# Max number of tokens allowed in code output:
MAX_SENSIBLE_OUTPUT_SIZE_TOKENS = Mutable(2500)

# GPT code environment:
TRACK_P_VALUES = Flag(True)  # must be True in the current version

""" MESSAGE FORMATTING: """
# Text width for conversation output:
TEXT_WIDTH = 150

# Whether to present code debugging iterations as code diff or full.
# Defining: compaction_code_diff = num_lines(new_code) - num_lines(code_diff)
# We show code diff if compaction_code_diff > MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF
MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF = Mutable(20)  # Use 0 to always show code diff, or None to always show full code

# Whether to show incomplete code in the output:
HIDE_INCOMPLETE_CODE = Flag(True)

""" PLAYBACK """
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

""" HUMAN CO-PILOTING """
# CHOSEN_APP:
#   'console': console-based interaction
#   'pyside': GUI-based interaction (requires installing PySide6)
#    None: Does not ask for or records human interactions (legacy. not recommended).
# Runs recorded with 'pyside'/'console' can be replayed with either 'pyside'/'console',
# but not with None. Runs recorded with None can be replayed only with None.
CHOSEN_APP = Mutable('pyside')

# Human review:
# NONE - no human review
# LLM_FIRST - LLM review is performed first and sent to human review
# LLM_UPON_REQUEST - LLM review is performed only upon human request
DEFAULT_HUMAN_REVIEW_TYPE = Mutable(HumanReviewType.LLM_UPON_REQUEST)

# AI review. If True, AI review will default to the terminating phrase exceeding the max_reviewing_rounds.
# (Only in effect when DEFAULT_HUMAN_REVIEW_TYPE is not HumanReviewType.NONE)
AUTO_TERMINATE_AI_REVIEW = Flag(False)

HUMAN_NAME = 'Human'

""" DEBUGGING """
SHOW_LLM_CONTEXT = Flag(True)
SAVE_INTERMEDIATE_LATEX = Flag(False)
PRINT_CITATIONS = Flag(True)
DEBUG_MODE = Flag(False)
