from __future__ import annotations

import os
from abc import ABCMeta
from dataclasses import dataclass
from typing import Union

from requests import Response

from data_to_paper.terminate.exceptions import TerminateException
from data_to_paper.text import dedent_triple_quote_str


@dataclass
class APIKey:
    key: str
    key_name: str

    @classmethod
    def from_env(cls, key_name: str) -> APIKey:
        key = os.environ.get(key_name)
        return cls(key, key_name)


@dataclass
class BaseServerErrorException(TerminateException, metaclass=ABCMeta):
    server: str


@dataclass
class ServerErrorException(BaseServerErrorException):
    """
    Error raised server wasn't able to respond.
    """
    response: Union[Response, Exception]

    def _get_response_as_str(self):
        try:
            return f'Server status code: {self.response.status_code}\n{self.response.reason}'
        except AttributeError:
            return str(self.response)

    def __str__(self):
        return f"Request to `{self.server}` server failed with the following error:\n```error\n" \
               f"{self._get_response_as_str()}\n```"


@dataclass
class BaseAPIKeyError(BaseServerErrorException, metaclass=ABCMeta):
    api_key: APIKey
    instructions: str = dedent_triple_quote_str("""
        To set up the API keys as environment variables on your system, see:
        https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
        """)


class MissingAPIKeyError(BaseAPIKeyError):
    def __str__(self):
        return \
            f"The API key for `{self.server}` is missing.\n" \
            f"You need to set the `{self.api_key.key_name}` environment variable.\n" \
            f"\n{self.instructions}"


@dataclass
class InvalidAPIKeyError(BaseAPIKeyError):
    response: Union[Response, Exception] = None

    def __str__(self):
        return \
            f"The API key for `{self.server}` is invalid.\n" \
            f"Trying to connect to the server with the key:\n`{self.api_key.key}`\n" \
            f"Connection failed with the following error:\n" \
            f"---\n```error\n{self.response}\n```\n---\n" \
            f"\n{self.instructions}"
