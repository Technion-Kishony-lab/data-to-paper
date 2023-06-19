import numpy as np
from _pytest.fixtures import fixture
from data_to_paper.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER, \
    SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER

@fixture
def query():
    return "the distance between the earth and the moon"


@fixture()
def paper():
    return {"paper_id": "",
            "title": "Hospital outbreak of Middle East respiratory syndrome",
            "abstract": "Between April 1 and May 23, 2013, a total of 23 cases of MERS-CoV ...",
            }


def test_semantic_scholar_get_papers(query):
    papers = SEMANTIC_SCHOLAR_SERVER_CALLER.get_server_response(query)
    assert len(papers) > 0


def test_semantic_scholar_get_paper_embedding(paper):
    embedding1 = SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER.get_server_response(paper)
    paper["paper_id"] = "123"
    embedding2 = SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER.get_server_response(paper)
    assert len(embedding1) > 0
    assert np.array_equal(embedding1, embedding2)
