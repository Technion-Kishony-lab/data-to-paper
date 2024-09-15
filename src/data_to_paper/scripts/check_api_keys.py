"""
Run this script to check if the API keys for the LLMServer and Semantic Scholar are valid.
"""

from data_to_paper.servers.check_connection import check_all_servers

if __name__ == '__main__':
    check_all_servers()
