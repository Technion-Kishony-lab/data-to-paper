"""
Run this script to check if the API keys for the LLMServer and Semantic Scholar are valid.
"""
from data_to_paper.latex.check_dependencies import check_all_pdflatex_dependencies
from data_to_paper.latex.latex_to_html import check_pandoc_is_installed
from data_to_paper.servers.check_connection import check_all_servers


def check_resources():
    print('\n\nChecking API keys and correct installation of all dependencies...')
    check_all_servers()
    check_all_pdflatex_dependencies()
    check_pandoc_is_installed()
