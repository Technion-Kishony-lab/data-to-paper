import os
from typing import Optional

from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils.mutable import Mutable, Flag

BASE_FOLDER_NAME = 'data-to-paper'

SUPPORTED_PACKAGES = ('numpy', 'pandas', 'scipy', 'sklearn', 'xgboost', 'imblearn')

OPENAI_API_BASE = "https://api.openai.com/v1"
DEEPINFRA_API_BASE = "https://api.deepinfra.com/v1/openai"

# OpenAI API keys. model=None is the default key.
OPENAI_MODELS_TO_ORGANIZATIONS_API_KEYS_AND_API_BASE_URL = dict[Optional[ModelEngine], str]({
    None:
        ("org-gvr0szNH28eeeuMCEG9JrwcR",
         "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",
         OPENAI_API_BASE),
    ModelEngine.GPT4:
        ("org-SplsVAouKqk9mWIpVgIIVwSD",
         "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",
         OPENAI_API_BASE),
    ModelEngine.GPT4_TURBO:
        ("org-SplsVAouKqk9mWIpVgIIVwSD",
         "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",
         OPENAI_API_BASE),
    ModelEngine.LLAMA_2_7b:
        ("",
         "Qkt0hDL5QZXndUfWcWckWRu0EBBQWlKG",
         DEEPINFRA_API_BASE),
    ModelEngine.LLAMA_2_70b:
        ("",
         "Qkt0hDL5QZXndUfWcWckWRu0EBBQWlKG",
         DEEPINFRA_API_BASE),
    ModelEngine.CODELLAMA:
        ("",
         "Qkt0hDL5QZXndUfWcWckWRu0EBBQWlKG",
         DEEPINFRA_API_BASE),
})

S2_API_KEY = "hqcN3JMNgl2Ue889JZ1Zd3ogYCjtdpta8V0OXv3c"

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

# Coalesce conversations with the same participants into one web-conversation:
COALESCE_WEB_CONVERSATIONS = Flag(True)

DELAY_SEND_TO_WEB = Mutable(0.1)  # seconds

# Products to send to client for the user to download:
PRODUCTS_TO_SEND_TO_CLIENT = ['paper.pdf', 'paper.tex']

# Human interactions:
RECORD_INTERACTIONS = Flag(True)
HUMAN_EDIT_CODE_REVIEW = True
HUMAN_NAME = 'Human'
CHOSEN_APP = Mutable('pyside')  # 'console', 'pyside', None
DELAY_APP_INTERACTION = Mutable(1)  # seconds

NUM_DIGITS_FOR_FLOATS = 4

os.environ['CLIENT_SERVER_MODE'] = 'False'


# GPT code environment:
TRACK_P_VALUES = Flag(True)

# Debugging switches:
SHOW_LLM_CONTEXT = Flag(True)
SAVE_INTERMEDIATE_LATEX = Flag(False)
PRINT_CITATIONS = Flag(True)
PRINT_COMMENTS = Flag(False)
