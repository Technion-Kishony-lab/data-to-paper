from _pytest.fixtures import fixture
from scientistgpt.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER

@fixture
def query():
    return "test query"


def test_semantic_scholar_get_papers(query):
    papers = SEMANTIC_SCHOLAR_SERVER_CALLER.get_server_response(query)
    assert len(papers) > 0