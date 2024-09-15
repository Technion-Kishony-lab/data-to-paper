from data_to_paper.latex.latex_to_pdf import is_pdflatex_installed
from data_to_paper.utils.resource_checking import resource_checking


@resource_checking("Checking pdflatex installation")
def check_pdflatex_is_installed():
    from .latex_doc import LatexDocument
    # This will raise MissingInstallationError
    LatexDocument().raise_if_pdflatex_is_not_installed()


@resource_checking("Checking pdflatex packages installation")
def check_pdflatex_packages_are_installed():
    from .latex_doc import LatexDocument
    # This will raise MissingInstallationError
    LatexDocument().raise_if_packages_are_not_installed()


def check_all_pdflatex_dependencies():
    check_pdflatex_is_installed()
    check_pdflatex_packages_are_installed()
