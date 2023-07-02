import functools
import os
import pickle
from abc import ABC

from pathlib import Path
from typing import Union

from .json import save_list_to_json, load_list_from_json


class NoMoreResponsesToMockError(Exception):
    pass


def convert_args_kwargs_to_tuple(args, kwargs):
    return args, tuple(sorted(kwargs.items()))


class ServerCaller(ABC):
    """
    A base class for calling a remote server, while allowing recording and replaying server responses.
    """

    name: str = None
    file_extension: str = None

    def __init__(self):
        self.old_records = self.empty_records
        self.new_records = self.empty_records
        self.args_kwargs_response_history = []  # for debugging
        self.is_playing_or_recording = False
        self.record_more_if_needed = False
        self.fail_if_not_all_responses_used = True
        self.should_save = False
        self.file_path = None

    @property
    def empty_records(self) -> Union[list, dict]:
        raise NotImplementedError()

    @property
    def all_records(self) -> Union[list, dict]:
        raise NotImplementedError()

    @staticmethod
    def _get_server_response(*args, **kwargs):
        """
        actual call to the server.
        this method should only return raw responses that can be serialized to json, without losing type information.
        """
        raise NotImplementedError()

    def _get_server_response_without_raising(self, *args, **kwargs):
        try:
            return self._get_server_response(*args, **kwargs)
        except Exception as e:
            return e

    @staticmethod
    def _post_process_response(response, args, kwargs):
        """
        post process the response before transmitting.
        """
        return response

    @staticmethod
    def _save_records(records, filepath):
        """
        saves the records to a file.
        """
        raise NotImplementedError()

    @staticmethod
    def _load_records(filepath):
        """
        loads the records from a file.
        """
        raise NotImplementedError()

    def get_server_response(self, *args, **kwargs):
        """
        returns the response from the server after post-processing. allows recording and replaying.
        """
        response = self._get_raw_server_response(*args, **kwargs)
        if isinstance(response, Exception):
            raise response
        return self._post_process_response(response, args, kwargs)

    def _get_response_from_records(self, args, kwargs):
        raise NotImplementedError()

    def _add_response_to_new_records(self, args, kwargs, response):
        raise NotImplementedError()

    def _get_raw_server_response(self, *args, **kwargs):
        """
        returns the raw response from the server, allows recording and replaying.
        """
        if not self.is_playing_or_recording:
            return self._get_server_response_without_raising(*args, **kwargs)
        response = self._get_response_from_records(args, kwargs)
        if response is None:
            if not self.record_more_if_needed:
                raise NoMoreResponsesToMockError()
            response = self._get_server_response_without_raising(*args, **kwargs)
            self._add_response_to_new_records(args, kwargs, response)
            if self.should_save:
                self.save_records(self.file_path)
        self.args_kwargs_response_history.append((args, kwargs, response))  # for debugging and testing
        return response

    def __enter__(self):
        self.new_records = self.empty_records
        self.is_playing_or_recording = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_playing_or_recording = False
        if self.should_save:
            self.save_records(self.file_path)
        return False  # do not suppress exceptions

    def mock(self, old_records=None, record_more_if_needed=True, fail_if_not_all_responses_used=True,
             should_save=False, file_path=None):
        """
        Returns a context manager to mock the server responses (specified as old_records).
        """
        self.old_records = old_records or self.empty_records
        self.args_kwargs_response_history = []
        self.record_more_if_needed = record_more_if_needed
        self.fail_if_not_all_responses_used = fail_if_not_all_responses_used
        self.should_save = should_save
        self.file_path = file_path
        return self

    def save_records(self, file_path):
        """
        Save the recorded responses to a file.
        """
        # create the directory if not exist
        Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
        self._save_records(self.all_records, file_path)

    def mock_with_file(self, file_path, record_more_if_needed=True, fail_if_not_all_responses_used=True,
                       should_save=True):
        """
        Returns a context-manager to mock the server responses from a specified file.
        """
        # load the old records from the file if exist
        if os.path.isfile(file_path):
            old_records = self._load_records(file_path)
        else:
            old_records = []

        return self.mock(old_records=old_records,
                         record_more_if_needed=record_more_if_needed,
                         fail_if_not_all_responses_used=fail_if_not_all_responses_used,
                         should_save=should_save,
                         file_path=file_path)

    def record_or_replay(self, file_path: Union[str, Path] = None, should_mock: bool = True):
        """
        Returns a decorator to call the decorated function while recording or replaying server responses.

        If the file exist, the responses will be replayed from the file.
        If the file does not exist, the responses will be recorded to the file.
        """

        def decorator(func):

            if not hasattr(func, '_module_file_path'):
                func._module_file_path = os.path.dirname(os.path.abspath(func.__code__.co_filename))

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                nonlocal file_path
                # use the file path of the decorated function if not given
                file_path = file_path or os.path.join(func._module_file_path, 'recorded_responses', func.__name__ +
                                                      self.file_extension)

                # run the test with the previous responses and record new responses
                with self.mock_with_file(file_path=file_path):
                    func(*args, **kwargs)

            wrapper._module_file_path = func._module_file_path
            return wrapper if should_mock else func

        return decorator


class ListServerCaller(ServerCaller, ABC):
    def __init__(self):
        super().__init__()
        self.index_in_old_records = 0

    @property
    def empty_records(self) -> list:
        return []

    @property
    def all_records(self):
        return self.old_records + self.new_records

    def _get_response_from_records(self, args, kwargs):
        if self.index_in_old_records < len(self.old_records):
            response = self.old_records[self.index_in_old_records]
            self.index_in_old_records += 1
            return response
        return None

    def _add_response_to_new_records(self, args, kwargs, response):
        self.new_records.append(response)

    @staticmethod
    def _save_records(records, filepath):
        save_list_to_json(records, filepath)

    @staticmethod
    def _load_records(filepath):
        return load_list_from_json(filepath)

    def __enter__(self):
        self.index_in_old_records = 0
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        results = super().__exit__(exc_type, exc_val, exc_tb)
        if self.fail_if_not_all_responses_used and self.index_in_old_records < len(self.old_records):
            raise AssertionError(f'Not all responses were used ({self.__class__.__name__}).')
        return results


class DictServerCaller(ServerCaller, ABC):

    @property
    def empty_records(self) -> dict:
        return {}

    @property
    def all_records(self):
        return self.old_records | self.new_records

    def _get_response_from_records(self, args, kwargs):
        tuple_args_and_kwargs = convert_args_kwargs_to_tuple(args, kwargs)
        return self.all_records.get(tuple_args_and_kwargs, None)

    def _add_response_to_new_records(self, args, kwargs, response):
        tuple_args_and_kwargs = convert_args_kwargs_to_tuple(args, kwargs)
        self.new_records[tuple_args_and_kwargs] = response

    @staticmethod
    def _save_records(records, filepath):
        with open(filepath, 'wb') as file:
            pickle.dump(records, file)

    @staticmethod
    def _load_records(filepath):
        with open(filepath, 'rb') as filepath:
            return pickle.load(filepath)
