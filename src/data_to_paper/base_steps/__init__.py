"""
Base classes to use for building each step in a multi-step process towards a goal.
"""

# --- PRODUCTS ---

# Products:

# Basic Products types:

# --- RUNNING MULTI-STEP PROCESS ---

# Base class for running multiple steps while accumulating Products towards a goal:
from .base_steps_runner import BaseStepsRunner, DataStepRunner

# In each step, we can use the Products from the previous step and choose
# from one of the base-classes below to create new Products.

# --- REQUESTING PRODUCTS FROM USER ---

# Base classes for requesting the user for products:
from .request_products_from_user import DirectorProductGPT


# --- REQUESTS PRODUCTS FROM LLM ---

# Requesting un-structured text:
from .base_products_conversers import BackgroundProductsConverser

# Requesting un-structured text as part of a gpt-gpt review process:
from .base_products_conversers import ReviewBackgroundProductsConverser

# Addon to check if response correctly extracts from provided products:
from .base_products_conversers import \
    CheckExtractionReviewBackgroundProductsConverser, CheckReferencedNumericReviewBackgroundProductsConverser

# Requesting quote-enclosed text (with optional gpt-review):
from .request_quoted_text import BaseProductsQuotedReviewGPT

# Requesting LaTeX formatted text (with optional gpt-review):
from .request_latex import LatexReviewBackgroundProductsConverser

# Requesting Python values (with optional gpt-review):
from .request_python_value import PythonValueReviewBackgroundProductsConverser
from .request_python_value import PythonDictReviewBackgroundProductsConverser
from .request_python_value import PythonDictWithDefinedKeysReviewBackgroundProductsConverser
from .request_python_value import PythonDictWithDefinedKeysAndValuesReviewBackgroundProductsConverser

# Requesting code (with automatic debugging feedback):
from .request_code import BaseCodeProductsGPT
from .debugger import DebuggerConverser

# Requesting answer to multiple choice question
from .request_multi_choice import MultiChoiceBackgroundProductsConverser

# Requesting literature search
from .request_literature_search import BaseLiteratureSearchReviewGPT
from .literature_search import LiteratureSearch

# --- CONVERTING PRODUCTS TO FILES ---

# Base classes for creating files from Products:
from .base_products_to_file import BaseFileProducer

# Base classes for creating PDFs from LaTeX Products:
from .latex_products_to_pdf import BaseLatexToPDF
