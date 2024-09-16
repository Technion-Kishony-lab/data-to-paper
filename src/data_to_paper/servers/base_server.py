import functools
import os
import pickle
import time
from abc import ABC
from pathlib import Path
from typing import Union, Optional

from data_to_paper.env import CHOSEN_APP, DELAY_SERVER_CACHE_RETRIEVAL
from .json_dump import dump_to_json, load_from_json
from .serialize_exceptions import serialize_exception, is_exception, de_serialize_exception


class NoMoreResponsesToMockError(Exception):
    pass


def recursively_convert_lists_and_dicts_to_tuples(obj):
    if isinstance(obj, (list, tuple)):
        return tuple(recursively_convert_lists_and_dicts_to_tuples(item) for item in obj)
    if isinstance(obj, dict):
        return tuple((recursively_convert_lists_and_dicts_to_tuples(key),
                      recursively_convert_lists_and_dicts_to_tuples(value)) for key, value in obj.items())
    return obj


def convert_args_kwargs_to_tuple(args, kwargs):
    return recursively_convert_lists_and_dicts_to_tuples((args, kwargs))


class ServerCaller(ABC):
    """
    A base class for calling a remote server, while allowing recording and replaying server responses.
    """

    name: str = None
    file_extension: str = None

    def __init__(self, fail_if_not_all_responses_used=True):
        self.old_records = self.empty_records
        self.new_records = self.empty_records
        self.args_kwargs_response_history = []  # for debugging
        self.is_playing_or_recording = False
        self.record_more_if_needed = False
        self.fail_if_not_all_responses_used = fail_if_not_all_responses_used
        self.should_save = False
        self.file_path = None

    @property
    def empty_records(self) -> Union[list, dict]:
        raise NotImplementedError()

    @property
    def all_records(self) -> Union[list, dict]:
        raise NotImplementedError()

    @classmethod
    def _get_server_response(cls, *args, **kwargs):
        """
        actual call to the server.
        this method should only return raw responses that can be serialized to json, without losing type information.
        """
        raise NotImplementedError()

    @staticmethod
    def _post_process_response(response, args, kwargs):
        """
        post process the response before transmitting.
        """
        return response

    def _save_records(self, records, filepath):
        """
        saves the records to a file.
        """
        raise NotImplementedError()

    def _load_records(self, filepath):
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
        """
        returns the response from the records, if exists.
        """
        raise NotImplementedError()

    def _add_response_to_new_records(self, args, kwargs, response):
        """
        adds a response to the new records.
        """
        raise NotImplementedError()

    def _get_raw_server_response(self, *args, **kwargs):
        """
        returns the raw response from the server, allows recording and replaying.
        """
        if not self.is_playing_or_recording:
            return self._get_server_response(*args, **kwargs)
        response = self._get_response_from_records(args, kwargs)
        if response is not None and CHOSEN_APP is not None:
            time.sleep(DELAY_SERVER_CACHE_RETRIEVAL.val)
        if response is None:
            if not self.record_more_if_needed:
                raise NoMoreResponsesToMockError()
            response = self._get_server_response(*args, **kwargs)
            self._add_response_to_new_records(args, kwargs, response)
            if self.should_save:
                self.save_records()
        self.args_kwargs_response_history.append((args, kwargs, response))  # for debugging and testing
        return response

    def __enter__(self):
        self.new_records = self.empty_records
        self.is_playing_or_recording = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_playing_or_recording = False
        if self.should_save:
            self.save_records()
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

    def save_records(self, file_path: Optional[str] = None):
        """
        Save the recorded responses to a file.
        """
        file_path = file_path or self.file_path
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

    def record_or_replay(self, file_path: Union[str, Path] = None, should_mock: bool = True,
                         fail_if_not_all_responses_used: bool = True):
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
                with self.mock_with_file(file_path=file_path,
                                         fail_if_not_all_responses_used=fail_if_not_all_responses_used):
                    func(*args, **kwargs)

            wrapper._module_file_path = func._module_file_path
            return wrapper if should_mock else func

        return decorator


class OrderedServerCaller(ServerCaller, ABC):
    """
    A base class for calling
    a remote server, while allowing recording and replaying server responses in the same order.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_in_old_records = 0

    def are_more_records_available(self):
        return self.index_in_old_records < len(self._get_old_records_as_list())

    def reset_index(self):
        self.index_in_old_records = 0

    def _get_old_records_as_list(self):
        """
        Return a single list of all the old records, as tuples of (key, value).
        """
        raise NotImplementedError()

    def _get_response_from_a_record(self, record, args, kwargs):
        return record

    def _get_response_from_records(self, args, kwargs):
        if self.are_more_records_available():
            record = self._get_old_records_as_list()[self.index_in_old_records]
            response = self._get_response_from_a_record(record, args, kwargs)
            self.index_in_old_records += 1
            return response
        return None

    @staticmethod
    def _serialize_record(record):
        if isinstance(record, Exception):
            return serialize_exception(record)
        return record

    @staticmethod
    def _deserialize_record(serialized_record):
        if is_exception(serialized_record):
            return de_serialize_exception(serialized_record)
        return serialized_record

    def __exit__(self, exc_type, exc_val, exc_tb):
        results = super().__exit__(exc_type, exc_val, exc_tb)
        if self.fail_if_not_all_responses_used and self.are_more_records_available():
            raise AssertionError(f'Not all responses were used ({self.__class__.__name__}).')
        return results

    def __enter__(self):
        self.reset_index()
        return super().__enter__()


class ListServerCaller(OrderedServerCaller):
    """
    A base class for calling a remote server, while allowing recording and replaying server responses.
    Records are saved as a sequence of responses and can be replayed in the same order (regardless of the arguments).
    """

    @property
    def empty_records(self) -> list:
        return []

    @property
    def all_records(self):
        return self.old_records + self.new_records

    def _get_old_records_as_list(self):
        return self.old_records

    def _add_response_to_new_records(self, args, kwargs, response):
        self.new_records.append(response)

    def _save_records(self, records, filepath):
        dump_to_json([self._serialize_record(record)
                      for record in records], filepath)

    def _load_records(self, filepath):
        return [self._deserialize_record(serialized_record)
                for serialized_record in load_from_json(filepath)]


class OrderedKeyToListServerCaller(OrderedServerCaller):
    """
    A class for calling a remote server, while allowing recording and replaying server responses.
    Records are saved as dictionary (key order preserving) of responses with ordered lists as values.
    """

    @property
    def empty_records(self) -> dict:
        return {}

    @property
    def all_records(self):
        records = self.old_records.copy()
        for key, values in self.new_records.items():
            records[key] = records.get(key, []) + values
        return records

    def _get_old_records_as_list(self):
        """
        Return a single list of all the old records, as tuples of (key, value).
        """
        return [(key, value) for key, values in self.old_records.items() for value in values]

    def _get_response_from_a_record(self, record, args, kwargs):
        # record is (key, value)
        key = self._generate_key(args, kwargs)
        if not key == record[0]:
            raise ValueError(f'Key mismatch: {key} != {record[0]}')
        return record[1]

    def _add_response_to_new_records(self, args, kwargs, response):
        key = self._generate_key(args, kwargs)
        if key not in self.new_records:
            self.new_records[key] = []
        self.new_records[key].append(response)

    def _generate_key(self, args, kwargs):
        return convert_args_kwargs_to_tuple(args, kwargs)

    def _save_records(self, records, filepath):
        serialized_records = \
            {key: [self._serialize_record(record) for record in value] for key, value in records.items()}
        dump_to_json(serialized_records, filepath)

    def _load_records(self, filepath):
        serialized_records = load_from_json(filepath)
        return {key:
                [self._deserialize_record(record) for record in value] for key, value in serialized_records.items()}

    def mock(self, old_records=None, *args, **kwargs):
        """
        Returns a context manager to mock the server responses (specified as old_records).
        """
        result = super().mock(old_records, *args, **kwargs)
        self.old_records = old_records if isinstance(old_records, dict) else {"GENERAL": old_records} if (
            old_records) else self.empty_records
        return result


class ParameterizedQueryServerCaller(ServerCaller, ABC):
    """
    A base class for calling a remote server, while allowing recording and replaying server responses.
    Records are saved as a dictionary of responses and can be replayed by the arguments and keyword arguments.
    """

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

    def _save_records(self, records, filepath):
        with open(filepath, 'wb') as file:
            pickle.dump(records, file)

    def _load_records(self, filepath):
        with open(filepath, 'rb') as filepath:
            return pickle.load(filepath)
