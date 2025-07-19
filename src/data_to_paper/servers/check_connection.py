import litellm
import numpy as np

from data_to_paper.env import (
    CODING_MODEL_ENGINE,
    JSON_MODEL_ENGINE,
    WRITING_MODEL_ENGINE,
)
from data_to_paper.servers.server_types import InvalidAPIKeyError
from data_to_paper.terminate.resource_checking import resource_checking

from data_to_paper.servers.semantic_scholar import (
    SEMANTIC_SCHOLAR_SERVER_CALLER,
    SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER,
)

models_to_check = {CODING_MODEL_ENGINE, JSON_MODEL_ENGINE, WRITING_MODEL_ENGINE}


EMBEDDING_PAPER = {
    "paper_id": "",
    "title": "Hospital outbreak of Middle East respiratory syndrome",
    "abstract": "Between April 1 and May 23, 2013, a total of 23 cases of MERS-CoV ...",
}


@resource_checking("Checking Semantic Scholar Citation-Server connection")
def check_semantic_scholar_connection():
    # Calling the server. Will raise ServerErrorException, InvalidAPIKeyError, or MissingAPIKeyError
    responses = SEMANTIC_SCHOLAR_SERVER_CALLER._get_server_response(
        query="antibiotics", rows=1
    )
    if len(responses) != 1:
        raise ConnectionError("Incorrect response from Semantic Scholar server.")


@resource_checking("Checking Semantic Scholar Embedding-Server connection")
def check_semantic_scholar_embedding_connection():
    # Calling the server. Will raise ServerErrorException, or MissingAPIKeyError
    responses = SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER._get_server_response(
        EMBEDDING_PAPER
    )
    if not isinstance(responses, np.ndarray):
        raise ConnectionError(
            "Incorrect response from Semantic Scholar Embedding server."
        )


@resource_checking("Checking LLM Servers connection")
def check_llm_servers_connection():
    for model_engine in models_to_check:
        print(f"Checking LLM Server connection for {model_engine}... ", end="")
        # Calling the server. Will raise ServerErrorException, InvalidAPIKeyError, or MissingAPIKeyError
        response = litellm.check_valid_key(
            model=model_engine.value, api_key=model_engine.api_key
        )
        if not response:
            raise InvalidAPIKeyError(
                server=model_engine.server_name,
                response=response,
                api_key=model_engine.api_key,
            )
        print("OK")


def check_all_servers():
    check_semantic_scholar_connection()
    check_semantic_scholar_embedding_connection()
    check_llm_servers_connection()


if __name__ == "__main__":
    check_llm_servers_connection()
