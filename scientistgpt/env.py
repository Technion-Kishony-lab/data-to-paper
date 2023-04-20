# SUPPORTED_PACKAGES = ['numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn', 'sklearn']
SUPPORTED_PACKAGES = ['numpy', 'pandas', 'scipy']

OPENAI_API_KEY = "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"

MODEL_ENGINE = "gpt-3.5-turbo"

# Text width for conversation output:
TEXT_WIDTH = 150

# max time for code timeout when running code from chatgpt (seconds)
MAX_EXEC_TIME = 200

# Decide whether to present code debugging iterations as code diff or full.
# Defining: compaction_code_diff = num_lines(new_code) - num_lines(code_diff)
# We show code diff if compaction_code_diff > MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF
MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF = 20  # Use 0 to always show code diff, or None to always show full code

# Decide whether to show incomplete code in the output:
HIDE_INCOMPLETE_CODE = True

# Max number of characters allowed in output txt file of gpt code:
MAX_SENSIBLE_OUTPUT_SIZE = 1000
