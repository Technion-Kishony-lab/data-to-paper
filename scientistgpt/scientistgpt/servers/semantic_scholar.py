import json
from dataclasses import dataclass
from typing import List, Dict

import numpy as np
import requests

from scientistgpt.env import S2_API_KEY
from scientistgpt.exceptions import ScientistGPTException
from scientistgpt.servers.base_server import ServerCaller
from scientistgpt.servers.crossref import ServerErrorCitationException

HEADERS = {
    'x-api-key': S2_API_KEY
}

PAPER_SEARCH_URL = 'https://api.semanticscholar.org/graph/v1/paper/search'
EMBEDDING_URL = 'https://model-apis.semanticscholar.org/specter/v1/invoke'


@dataclass
class ServerErrorNoMatchesFoundForQuery(ScientistGPTException):
    """
    Error raised server wasn't able to find any matches for the query.
    """
    query: str

    def __str__(self):
        return f"Server wasn't able to find any matches for the query:\n {self.query}\n please try a different query."


class SemanticScholarPaperServerCaller(ServerCaller):
    """
    Search for citations with abstracts in Semantic Scholar.
    """

    file_extension = "_semanticscholar_paper.txt"

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

        response = requests.get(PAPER_SEARCH_URL, headers=HEADERS, params=params)

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


class SemanticScholarEmbeddingServerCaller(ServerCaller):
    """
    Embed "paper" (title + abstract) using SPECTER Semantic Scholar API.
    """

    file_extension = "_semanticscholar_embedding.txt"
    max_batch_size = 16

    @staticmethod
    def chunks(lst, chunk_size=max_batch_size):
        """Splits a longer list to respect batch size"""
        for i in range(0, len(lst), chunk_size):
            yield lst[i: i + chunk_size]

    @staticmethod
    def _get_server_response(paper: Dict[str, str]) -> np.ndarray:
        """
        Send the paper to the SPECTER Semantic Scholar API and get the embedding.
        """
        # check that the paper has id, title and abstract attributes, if not raise an error
        if not all(key in paper for key in ["paper_id", "title", "abstract"]):
            raise ValueError("Paper must have 'paper_id', 'title' and 'abstract' attributes.")

        response = requests.post(EMBEDDING_URL, json=[paper])

        if response.status_code != 200:
            raise ServerErrorCitationException(status_code=response.status_code, text=response.text)

        paper_embedding = response.json()["preds"][0]["embedding"]

        return np.array(paper_embedding)

    @staticmethod
    def _post_process_response(response):
        """
        Post process the response from the server.
        """
        return response


SEMANTIC_SCHOLAR_SERVER_CALLER = SemanticScholarPaperServerCaller()
SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER = SemanticScholarEmbeddingServerCaller()
