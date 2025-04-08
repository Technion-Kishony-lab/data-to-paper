from data_to_paper.servers.check_connection import (
    check_semantic_scholar_connection,
    check_llm_servers_connection,
    check_all_servers,
)
from data_to_paper.servers.types import (
    InvalidAPIKeyError,
    MissingSemanticScholarAPIKeyError,
)


def test_check_all_servers():
    check_all_servers()


def test_semantic_scholar_server_caller_get_server_response_with_wrong_api_key():
    from data_to_paper.env import SEMANTIC_SCHOLAR_API_KEY

    original_key = SEMANTIC_SCHOLAR_API_KEY.key
    try:
        SEMANTIC_SCHOLAR_API_KEY.key = "wrong_key"
        check_semantic_scholar_connection()
    except InvalidAPIKeyError as e:
        assert "invalid" in str(e)
        assert "wrong_key" in str(e)
        print(e)
    finally:
        SEMANTIC_SCHOLAR_API_KEY.key = original_key


def test_semantic_scholar_server_caller_get_server_response_with_missing_api_key():
    from data_to_paper.env import SEMANTIC_SCHOLAR_API_KEY

    original_key = SEMANTIC_SCHOLAR_API_KEY.key
    try:
        SEMANTIC_SCHOLAR_API_KEY.key = None
        check_semantic_scholar_connection()
    except MissingSemanticScholarAPIKeyError as e:
        assert "SEMANTIC SCHOLAR API key is missing" in str(e)
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
        assert "wrong_key" in str(e)
        print(e)
    finally:
        SEMANTIC_SCHOLAR_API_KEY.key = original_key
