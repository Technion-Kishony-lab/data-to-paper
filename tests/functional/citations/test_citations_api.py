from scientistgpt.gpt_interactors.citation_adding.call_crossref import CROSSREF_SERVER_CALLER

QUERY = 'covid-19 affected the world'


@CROSSREF_SERVER_CALLER.record_or_replay()
def test_get_crossref_response():
    citations = CROSSREF_SERVER_CALLER.get_server_response(QUERY)

    assert len(citations) > 0
