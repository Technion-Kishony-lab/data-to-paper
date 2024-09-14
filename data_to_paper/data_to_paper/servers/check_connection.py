import colorama
import numpy as np

from data_to_paper.env import CODING_MODEL_ENGINE, JSON_MODEL_ENGINE, WRITING_MODEL_ENGINE
from data_to_paper.utils.highlighted_text import colored_text
from data_to_paper.conversation import Message, Role

from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER
from data_to_paper.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER, \
    SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER

models_to_check = {CODING_MODEL_ENGINE, JSON_MODEL_ENGINE, WRITING_MODEL_ENGINE}


EMBEDDING_PAPER = {
    "paper_id": "",
    "title": "Hospital outbreak of Middle East respiratory syndrome",
    "abstract": "Between April 1 and May 23, 2013, a total of 23 cases of MERS-CoV ...",
}


def server_checking(func):
    def wrapper(*args, **kwargs):
        print(f"\nRunning {func.__name__} ...")
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(colored_text(f"Connection failed:\n{e}", color=colorama.Fore.RED))
            return
        print(colored_text("Connection successful!", color=colorama.Fore.GREEN))
    return wrapper


@server_checking
def check_semantic_scholar_connection():
    responses = SEMANTIC_SCHOLAR_SERVER_CALLER._get_server_response(query='antibiotics', rows=1)
    if len(responses) != 1:
        raise ConnectionError("Incorrect response from Semantic Scholar server.")


@server_checking
def check_semantic_scholar_embedding_connection():
    responses = SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER._get_server_response(EMBEDDING_PAPER)
    if not isinstance(responses, np.ndarray):
        raise ConnectionError("Incorrect response from Semantic Scholar Embedding server.")


@server_checking
def check_llm_servers_connection():
    for model_engine in models_to_check:
        response = OPENAI_SERVER_CALLER._get_server_response(
            messages=[Message(role=Role.USER, content='Your favorite color. Answer in one word')],
            model_engine=model_engine)
        if len(response.value) == 0:
            raise ConnectionError("Incorrect response from OpenAI server.")


def check_all_servers():
    check_semantic_scholar_connection()
    check_semantic_scholar_embedding_connection()
    check_llm_servers_connection()
