from typing import Optional

from scientistgpt.servers.openai_models import ModelEngine
from scientistgpt.utils.mutable import Mutable, Flag
from scientistgpt.utils.nice_list import NiceList

SUPPORTED_PACKAGES = ('numpy', 'pandas', 'scipy', 'sklearn', 'xgboost', 'imblearn')

# OpenAI API keys. model=None is the default key.
OPENAI_MODELS_TO_ORGANIZATIONS_AND_API_KEYS = dict[Optional[ModelEngine], str]({
    None:
        ("org-gvr0szNH28eeeuMCEG9JrwcR",
         "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"),
    ModelEngine.GPT4:
        ("org-SplsVAouKqk9mWIpVgIIVwSD",
         "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"),
})

DEFAULT_MODEL_ENGINE = ModelEngine.GPT35_TURBO
MAX_MODEL_ENGINE = ModelEngine.GPT4_32

# Text width for conversation output:
TEXT_WIDTH = 150

# max time for code timeout when running code from chatgpt (seconds)
MAX_EXEC_TIME = Mutable(200)

# Decide whether to present code debugging iterations as code diff or full.
# Defining: compaction_code_diff = num_lines(new_code) - num_lines(code_diff)
# We show code diff if compaction_code_diff > MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF
MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF = Mutable(20)  # Use 0 to always show code diff, or None to always show full code

# Decide whether to show incomplete code in the output:
HIDE_INCOMPLETE_CODE = Flag(True)

# Max number of characters allowed in output txt file of gpt code:
MAX_SENSIBLE_OUTPUT_SIZE = Mutable(6000)

# Coalesce conversations with the same participants into one web-conversation:
COALESCE_WEB_CONVERSATIONS = Flag(True)

DELAY_AUTOMATIC_RESPONSES = Mutable(0.1)  # seconds

DEBUG = Flag(True)
