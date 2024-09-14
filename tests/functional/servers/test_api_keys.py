from data_to_paper.servers.check_connection import check_semantic_scholar_connection, \
    check_llm_servers_connection
from data_to_paper.servers.types import InvalidAPIKeyError


def test_semantic_scholar_server_caller_get_server_response():
    check_semantic_scholar_connection()


def test_openai_server_caller_get_server_response():
    check_llm_servers_connection()


def test_semantic_scholar_server_caller_get_server_response_ith_wrong_api_key():
    from data_to_paper.env import SEMANTIC_SCHOLAR_API_KEY
    original_key = SEMANTIC_SCHOLAR_API_KEY.key
    try:
        SEMANTIC_SCHOLAR_API_KEY.key = "wrong_key"
        check_semantic_scholar_connection()
    except InvalidAPIKeyError as e:
        assert "invalid" in str(e)
        assert 'wrong_key' in str(e)
        print(e)
    finally:
        SEMANTIC_SCHOLAR_API_KEY.key = original_key


def test_openai_server_caller_get_server_response_with_wrong_api_key():
    from data_to_paper.env import SEMANTIC_SCHOLAR_API_KEY
    original_key = SEMANTIC_SCHOLAR_API_KEY.key
    try:
        SEMANTIC_SCHOLAR_API_KEY.key = "wrong_key"
        check_llm_servers_connection()
    except InvalidAPIKeyError as e:
        assert "invalid" in str(e)
        assert 'wrong_key' in str(e)
        print(e)
    finally:
        SEMANTIC_SCHOLAR_API_KEY.key = original_key
