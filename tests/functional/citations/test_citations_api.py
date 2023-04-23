from scientistgpt.gpt_interactors.citation_adding.call_crossref import CrossrefServerCaller, CROSSREF_SERVER_CALLER

QUERY = 'covid-19 affected the world'


@CROSSREF_SERVER_CALLER.record_or_replay()
def test_get_crossref_response():
    crossref_server_caller = CrossrefServerCaller()
    citations = crossref_server_caller.get_server_response(QUERY)

    assert len(citations) > 0
