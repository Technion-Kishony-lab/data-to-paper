import logging
import os
import re
import sys
from contextlib import contextmanager

from plasTeX.TeX import TeX
from plasTeX.Renderers.HTML5 import HTML5

from data_to_paper.utils.file_utils import run_in_temp_directory

# Your LaTeX document as a string
LATEX_BEGIN = r"""
\documentclass{article}
\begin{document}
"""

LATEX_END = r"""
\end{document}
"""

@contextmanager
def suppress_logging(level=logging.ERROR):
    previous_level = logging.getLogger().getEffectiveLevel()
    logging.getLogger().setLevel(level)
    try:
        yield
    finally:
        logging.getLogger().setLevel(previous_level)


@contextmanager
def suppress_stdout_stderr():
    """A context manager that redirects stdout, stderr and logging to devnull."""
    with open(os.devnull, 'w') as fnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        old_logging_level = logging.root.manager.disable

        sys.stdout, sys.stderr = fnull, fnull
        logging.disable(logging.CRITICAL)  # Suppresses all logging calls with severity 'CRITICAL' and lower

        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            logging.disable(old_logging_level)  # Restore the old logging level


def convert_latex_to_html(latex: str) -> str:
    """
    Convert LaTeX to HTML using plasTeX
    """
    # Initialize a TeX processor and parse the document
    with suppress_stdout_stderr():
        tex = TeX()
        tex.ownerDocument.config['files']['split-level'] = -100  # Prevents document splitting
        tex.input(LATEX_BEGIN + latex + LATEX_END)
        document = tex.parse()
        renderer = HTML5()

        with run_in_temp_directory():
            renderer.render(document)
            # read the index.html file
            with open('index.html') as f:
                html = f.read()

    # Remove numeric "1", "2" in headers: h1, h2, h3, h4
    html = re.sub(pattern=r'(<h[1-6][^>]*>)[0-9]+\.?\s*', repl=r'\1', string=html)

    return html
