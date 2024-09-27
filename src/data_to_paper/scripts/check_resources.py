"""
Run this script to check if the API keys for the LLMServer and Semantic Scholar are valid.
"""
from data_to_paper.latex.check_dependencies import check_all_pdflatex_dependencies
from data_to_paper.latex.latex_to_html import check_pandoc_is_installed
from data_to_paper.scripts.run import extract_version_from_toml
from data_to_paper.servers.check_connection import check_all_servers


def check_resources():
    print(f'\n\n** data-to-paper version {extract_version_from_toml()} **\n')
    print('RESOURCE CHECKS\n')
    print('Checking external server connections, API keys, and installation dependencies...\n')
    check_all_servers()
    check_all_pdflatex_dependencies()
    check_pandoc_is_installed()
