from dataclasses import dataclass
from typing import List

import requests

from scientistgpt.env import S2_API_KEY
from scientistgpt.exceptions import ScientistGPTException
from scientistgpt.servers.base_server import ServerCaller
from scientistgpt.servers.crossref import ServerErrorCitationException

HEADERS = {
    'x-api-key': S2_API_KEY
}

S2_URL = 'https://api.semanticscholar.org/graph/v1/paper/search'


@dataclass
class ServerErrorNoMatchesFoundForQuery(ScientistGPTException):
    """
    Error raised server wasn't able to find any matches for the query.
    """
    query: str

    def __str__(self):
        return f"Server wasn't able to find any matches for the query:\n {self.query}\n please try a different query."


class SemanticScholarServerCaller(ServerCaller):
    """
    Search for citations with abstracts in Semantic Scholar.
    """

    file_extension = "_semanticscholar.txt"

    @staticmethod
    def _get_server_response(query, rows=4) -> List[dict]:
        """
        Get the response from the semantic scholar server as a list of dict citation objects.
        """
        params = {
            "query": query,
            "limit": rows,
            "fields": "title,url,abstract,embedding,tldr",
        }

        response = requests.get(S2_URL, headers=HEADERS, params=params)

        if response.status_code != 200:
            raise ServerErrorCitationException(status_code=response.status_code, text=response.text)

        data = response.json()
        total = data["total"]
        if total == 0:
            raise ServerErrorNoMatchesFoundForQuery(query=query)
        papers = data["data"]

        return papers

    @staticmethod
    def _post_process_response(response):
        """
        Post process the response from the server.
        """

        return response



SEMANTIC_SCHOLAR_SERVER_CALLER = SemanticScholarServerCaller()
