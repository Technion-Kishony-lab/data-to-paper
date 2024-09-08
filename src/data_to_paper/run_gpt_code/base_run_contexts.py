from __future__ import annotations

import os
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
from typing import List, Type, TypeVar, Optional, Iterable

from .user_script_name import is_called_from_user_script, is_called_from_data_to_paper
from .run_issues import RunIssues

T = TypeVar('T', bound='SingletonRegisteredRunContext')


@dataclass
class DisableableContext:
    """
    Context manager that can be temporarily disabled.
    """
    TEMPORARILY_DISABLE_IS_INTERNAL_ONLY = False
    # Whether temporarily_disable() is only for the internal state of the context manager, or completely
    # reversing the __enter__ and __exit__ methods.

    _is_enabled: Optional[bool] = None

    def _reversible_enter(self):
        pass

    def _reversible_exit(self):
        pass

    def __enter__(self):
        self._reversible_enter()
        self._is_enabled = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._is_enabled = None
        self._reversible_exit()
        return False

    @contextmanager
    def temporarily_disable(self, internal_only: bool = None):

        assert self._is_enabled is not None, 'The context is not initialized yet.'

        internal_only = internal_only if internal_only is not None else self.TEMPORARILY_DISABLE_IS_INTERNAL_ONLY
        was_enabled = self._is_enabled

        if was_enabled:
            if not internal_only:
                self._reversible_exit()
            self._is_enabled = False
        try:
            yield
        finally:
            if was_enabled:
                if not internal_only:
                    self._reversible_enter()
                self._is_enabled = True


@dataclass
class RunContext(DisableableContext):
    """
    Base context manager for running GPT code.
    """
    issues: Optional[RunIssues] = None
    name: Optional[str] = None

    def __enter__(self):
        self.issues = RunIssues()
        return super().__enter__()

    def _is_called_from_user_script(self, offset: int = 3) -> bool:
        """
        Check if the code is called from user script.
        """
        return is_called_from_user_script(offset=offset + 1)

    def _is_called_from_data_to_paper(self, offset: int = 3) -> bool:
        """
        Check if the code is called from data_to_paper.
        """
        return is_called_from_data_to_paper(offset=offset + 1)


@dataclass
class RegisteredRunContext(RunContext):
    """
    Base context manager for running GPT code that can be registered to be accessed from anywhere.
    Allows centralized `temporarily_disable_all` registered context managers.
    """
    PROCESS_AND_NAME_TO_OBJECT = {}
    should_register: bool = True

    @property
    def _process_and_identifier(self):
        return os.getpid(), self._identifier

    @property
    def _identifier(self):
        return id(self)

    def __enter__(self):
        if self.should_register:
            self.PROCESS_AND_NAME_TO_OBJECT[self._process_and_identifier] = self
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.should_register:
            del self.PROCESS_AND_NAME_TO_OBJECT[self._process_and_identifier]
        return super().__exit__(exc_type, exc_val, exc_tb)

    @classmethod
    def get_all_runtime_instances(cls) -> List[RegisteredRunContext]:
        process_id = os.getpid()
        return [obj for (pid, _), obj in cls.PROCESS_AND_NAME_TO_OBJECT.items() if pid == process_id]

    @staticmethod
    @contextmanager
    def temporarily_disable_all():
        """
        Context manager for temporarily disabling all registered runtime contexts.
        """
        objs = RegisteredRunContext.get_all_runtime_instances()
        with ExitStack() as stack:
            for obj in objs:
                stack.enter_context(obj.temporarily_disable())
            yield


@dataclass
class SingletonRegisteredRunContext(RegisteredRunContext):
    """
    Base context manager for running GPT code that only exists once per class.
    Allows accessing the runtime instance from the class.
    """

    @property
    def _identifier(self):
        return self.__class__.__name__

    @classmethod
    def get_runtime_instance(cls: Type[T]) -> T:
        process_and_identifier = os.getpid(), cls.__name__
        if process_and_identifier not in cls.PROCESS_AND_NAME_TO_OBJECT:
            raise RuntimeError(f'SingletonRegisteredRunContext {cls.__name__} was not created yet.')
        return cls.PROCESS_AND_NAME_TO_OBJECT[process_and_identifier]


@dataclass
class MultiRunContext(RunContext):
    """
    Pack together multiple run contexts.
    """
    contexts: Iterable[RunContext] = ()

    def __enter__(self):
        for context in self.contexts:
            context.__enter__()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for context in self.contexts:
            context.__exit__(exc_type, exc_val, exc_tb)
            self.issues.extend(context.issues)
        return super().__exit__(exc_type, exc_val, exc_tb)
