"""
Base classes to use for building each step in a multi-step process towards a goal.
"""

# --- PRODUCTS ---

# Products:

# Basic Products types:

# --- RUNNING MULTI-STEP PROCESS ---

# Base class for running multiple steps while accumulating Products towards a goal:
from .base_steps_runner import BaseStepsRunner

# In each step, we can use the Products from the previous step and choose
# from one of the base-classes below to create new Products.

# --- REQUESTING PRODUCTS FROM USER ---

# Base classes for requesting the user for products:
from .request_products_from_user import DirectorProductGPT


# --- REQUESTS PRODUCTS FROM CHATGPT ---

# Requesting un-structured text:
from .base_products_conversers import BaseBackgroundProductsGPT

# Requesting un-structured text as part of a gpt-gpt review process:
from .base_products_conversers import BaseProductsReviewGPT

# Addon to check if response correctly extracts from provided products:
from .base_products_conversers import BaseCheckExtractionProductsReviewGPT

# Requesting quote-enclosed text (with optional gpt-review):
from .request_quoted_text import BaseProductsQuotedReviewGPT

# Requesting LaTeX formatted text (with optional gpt-review):
from .request_latex import BaseLatexProductsReviewGPT

# Requesting Python values (with optional gpt-review):
from .request_python_value import BasePythonValueProductsReviewGPT

# Requesting code (with automatic debugging feedback):
from .request_code import BaseCodeProductsGPT, OfferRevisionCodeProductsGPT, DataframeChangingCodeProductsGPT


# --- CONVERTING PRODUCTS TO FILES ---

# Base classes for creating files from Products:
from .base_products_to_file import BaseFileProducer

# Base classes for creating PDFs from LaTeX Products:
from .latex_products_to_pdf import BaseLatexToPDF, BaseLatexToPDFWithAppendix
