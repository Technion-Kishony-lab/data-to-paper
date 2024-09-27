from data_to_paper.terminate.resource_checking import resource_checking
from .latex_doc import LatexDocument


@resource_checking("Checking pdflatex installation")
def check_pdflatex_is_installed():
    # This will raise MissingInstallationError
    LatexDocument().raise_if_pdflatex_is_not_installed()


@resource_checking("Checking pdflatex packages installation")
def check_pdflatex_packages_are_installed():
    # This will raise MissingInstallationError
    LatexDocument().raise_if_packages_are_not_installed()


def check_all_pdflatex_dependencies():
    check_pdflatex_is_installed()
    check_pdflatex_packages_are_installed()
