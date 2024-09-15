import os

from typing import Union

import pytest

from data_to_paper.servers.base_server import ListServerCaller, ParameterizedQueryServerCaller, \
    NoMoreResponsesToMockError, convert_args_kwargs_to_tuple, OrderedKeyToListServerCaller


class TestListServerCaller(ListServerCaller):
    @classmethod
    def _get_server_response(cls, response: Union[str, Exception] = 'response'):
        if isinstance(response, Exception):
            raise response
        return response


class TestParameterizedQueryServerCaller(ParameterizedQueryServerCaller):
    @classmethod
    def _get_server_response(cls, response: Union[str, Exception] = 'response'):
        if isinstance(response, Exception):
            raise response
        return response


class TestOrderedKeyToListServerCaller(OrderedKeyToListServerCaller):
    @classmethod
    def _get_server_response(cls, key: str, response: Union[str, Exception] = 'response'):
        if isinstance(response, Exception):
            raise response
        return response

    def _generate_key(self, args, kwargs):
        return args[0]


def test_list_server_mock_responses():
    server = TestListServerCaller()
    with server.mock(old_records=['response1', 'response2']) as mock:
        assert mock.get_server_response() == 'response1'
        assert mock.get_server_response() == 'response2'


def test_dict_server_mock_responses():
    server = TestParameterizedQueryServerCaller()
    with server.mock(old_records={convert_args_kwargs_to_tuple(('arg1', ), {}): 'response1',
                                  convert_args_kwargs_to_tuple(('arg2', ), {}): 'response2'}) as mock:
        assert mock.get_server_response('arg1') == 'response1'
        assert mock.get_server_response('arg2') == 'response2'
        assert mock.get_server_response('arg1') == 'response1'


def test_ordered_key_server_mock_responses():
    server = TestOrderedKeyToListServerCaller()
    with server.mock(old_records={'key1': ['response1', 'response2'], 'key2': ['response3']}) as mock:
        assert mock.get_server_response('key1') == 'response1'
        assert mock.get_server_response('key1') == 'response2'
        assert mock.get_server_response('key2') == 'response3'


def test_ordered_key_server_mock_responses_raise_on_incorrect_key():
    server = TestOrderedKeyToListServerCaller()
    with server.mock(old_records={'key1': ['response1', 'response2'], 'key2': ['response3']},
                     fail_if_not_all_responses_used=False) as mock:
        assert mock.get_server_response('key1') == 'response1'
        with pytest.raises(ValueError):
            mock.get_server_response('key2')


def test_list_server_mock_exception_when_no_responses_left():
    server = TestListServerCaller()
    with server.mock(old_records=['response1'], record_more_if_needed=False) as mock:
        assert mock.get_server_response() == 'response1'
        with pytest.raises(NoMoreResponsesToMockError):
            mock.get_server_response()


def test_ordered_key_server_mock_exception_when_no_responses_left():
    server = TestOrderedKeyToListServerCaller()
    with server.mock(old_records={'key1': ['response1']}, record_more_if_needed=False) as mock:
        assert mock.get_server_response('key1') == 'response1'
        with pytest.raises(NoMoreResponsesToMockError):
            mock.get_server_response('key1')


def test_dict_server_mock_exception_when_no_responses_matching():
    server = TestParameterizedQueryServerCaller()
    with server.mock(old_records={convert_args_kwargs_to_tuple(('arg1', ), {}): 'response1',
                                  convert_args_kwargs_to_tuple(('arg2', ), {}): 'response2'},
                     record_more_if_needed=False) as mock:
        assert mock.get_server_response('arg1') == 'response1'
        with pytest.raises(NoMoreResponsesToMockError):
            mock.get_server_response('arg3')


def test_server_mock_records_when_runs_out_of_responses():
    server = TestListServerCaller()
    with server.mock(old_records=['response1'], record_more_if_needed=True) as mock:
        assert mock.get_server_response() == 'response1'
        assert mock.get_server_response() == 'response'
        assert mock.new_records == ['response']


def test_dict_server_mock_records_when_args_not_matching_records():
    server = TestParameterizedQueryServerCaller()
    with server.mock(old_records={convert_args_kwargs_to_tuple(('arg1', ), {}): 'response1',
                                  convert_args_kwargs_to_tuple(('arg2', ), {}): 'response2'},
                     record_more_if_needed=True) as mock:
        assert mock.get_server_response('arg1') == 'response1'
        assert mock.get_server_response('arg3') == 'arg3'
        assert mock.new_records == {convert_args_kwargs_to_tuple(('arg3', ), {}): 'arg3'}


def test_mock_server_exception():
    server = TestListServerCaller()
    with server.mock(old_records=[Exception('exception1'), Exception('exception2')]) as mock:
        with pytest.raises(Exception) as e:
            mock.get_server_response()
        assert str(e.value) == 'exception1'
        with pytest.raises(Exception) as e:
            mock.get_server_response()
        assert str(e.value) == 'exception2'


def test_mock_server_save_load_responses_to_file(tmpdir):
    server = TestListServerCaller()
    file_path = os.path.join(tmpdir, 'responses.txt')
    responses = ['response1', 'response2', 'response3']
    with server.mock(file_path=file_path, should_save=True) as mock:
        for response in responses:
            assert mock.get_server_response(response) == response

    for i in range(2):
        new_server = TestListServerCaller()
        with new_server.mock_with_file(file_path=file_path) as mock:
            for response in responses:
                assert mock.get_server_response(response) == response


def test_mock_server_saves_upon_error(tmpdir):
    server = TestListServerCaller()
    file_path = os.path.join(tmpdir, 'responses.txt')
    try:
        with server.mock(file_path=file_path, should_save=True) as mock:
            assert mock.get_server_response('response1') == 'response1'
            raise KeyboardInterrupt('exception1')
    except KeyboardInterrupt:
        pass
    new_server = TestListServerCaller()
    with new_server.mock_with_file(file_path=file_path) as mock:
        assert mock.get_server_response() == 'response1'
