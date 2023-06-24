from abc import ABC, abstractmethod
from typing import Optional


DEFAULT_PROMPT = "You are a helpful {role_name}."

class Role(ABC):
    name: str
    initial_prompt: str

    def __init__(self, role_name: str, custom_prompt: Optional[str] = None):
        self.name = role_name
        self.initial_prompt = DEFAULT_PROMPT
        if custom_prompt is not None:
            self.initial_prompt = custom_prompt

    def generate_prompt(self) -> str:
        chat_prompt = self.initial_prompt.format(role_name=self.name)
        return  chat_prompt
