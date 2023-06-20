import os

from typing import Union

import pytest

from data_to_paper.servers.base_server import ListServerCaller, DictServerCaller, \
    NoMoreResponsesToMockError, convert_args_kwargs_to_tuple


class MockServer(ListServerCaller):
    @staticmethod
    def _get_server_response(response: Union[str, Exception] = 'response'):
        if isinstance(response, Exception):
            raise response
        return response


class DictMockServer(DictServerCaller):
    @staticmethod
    def _get_server_response(response: Union[str, Exception] = 'response'):
        if isinstance(response, Exception):
            raise response
        return response


def test_server_mock_responses():
    server = MockServer()
    with server.mock(old_records=['response1', 'response2']) as mock:
        assert mock.get_server_response() == 'response1'
        assert mock.get_server_response() == 'response2'


def test_dict_server_mock_responses():
    server = DictMockServer()
    with server.mock(old_records={convert_args_kwargs_to_tuple(('arg1', ), {}): 'response1',
                                  convert_args_kwargs_to_tuple(('arg2', ), {}): 'response2'}) as mock:
        assert mock.get_server_response('arg1') == 'response1'
        assert mock.get_server_response('arg2') == 'response2'
        assert mock.get_server_response('arg1') == 'response1'


def test_server_mock_exception_when_no_responses_left():
    server = MockServer()
    with server.mock(old_records=['response1'], record_more_if_needed=False) as mock:
        assert mock.get_server_response() == 'response1'
        with pytest.raises(NoMoreResponsesToMockError):
            mock.get_server_response()


def test_dict_server_mock_exception_when_no_responses_matching():
    server = DictMockServer()
    with server.mock(old_records={convert_args_kwargs_to_tuple(('arg1', ), {}): 'response1',
                                  convert_args_kwargs_to_tuple(('arg2', ), {}): 'response2'},
                     record_more_if_needed=False) as mock:
        assert mock.get_server_response('arg1') == 'response1'
        with pytest.raises(NoMoreResponsesToMockError):
            mock.get_server_response('arg3')


def test_server_mock_records_when_runs_out_of_responses():
    server = MockServer()
    with server.mock(old_records=['response1'], record_more_if_needed=True) as mock:
        assert mock.get_server_response() == 'response1'
        assert mock.get_server_response() == 'response'
        assert mock.new_records == ['response']


def test_dict_server_mock_records_when_args_not_matching_records():
    server = DictMockServer()
    with server.mock(old_records={convert_args_kwargs_to_tuple(('arg1', ), {}): 'response1',
                                  convert_args_kwargs_to_tuple(('arg2', ), {}): 'response2'},
                     record_more_if_needed=True) as mock:
        assert mock.get_server_response('arg1') == 'response1'
        assert mock.get_server_response('arg3') == 'arg3'
        assert mock.new_records == {convert_args_kwargs_to_tuple(('arg3', ), {}): 'arg3'}


def test_mock_server_exception():
    server = MockServer()
    with server.mock(old_records=[Exception('exception1'), Exception('exception2')]) as mock:
        with pytest.raises(Exception) as e:
            mock.get_server_response()
        assert str(e.value) == 'exception1'
        with pytest.raises(Exception) as e:
            mock.get_server_response()
        assert str(e.value) == 'exception2'


def test_mock_server_records_exceptions():
    server = MockServer()
    with server.mock(old_records=[Exception('exception1')], record_more_if_needed=True) as mock:
        with pytest.raises(Exception) as e:
            mock.get_server_response()
        assert str(e.value) == 'exception1'
        with pytest.raises(ValueError):
            mock.get_server_response(ValueError('exception2'))
        recording = mock.new_records[0]
        assert isinstance(recording, ValueError) and str(recording) == 'exception2'


def test_mock_server_save_load_responses_to_file(tmpdir):
    server = MockServer()
    file_path = os.path.join(tmpdir, 'responses.txt')
    responses = ['response1', ValueError('exception1'), 'response2', ValueError('exception2'), ValueError('exception3')]
    with server.mock(file_path=file_path, should_save=True) as mock:
        for response in responses:
            if isinstance(response, Exception):
                with pytest.raises(type(response)) as e:
                    mock.get_server_response(response)
                assert str(e.value) == str(response)
            else:
                assert mock.get_server_response(response) == response

    for i in range(2):
        new_server = MockServer()
        with new_server.mock_with_file(file_path=file_path) as mock:
            for response in responses:
                if isinstance(response, Exception):
                    with pytest.raises(type(response)) as e:
                        mock.get_server_response(response)
                    assert str(e.value) == str(response)
                    assert e.value.args == response.args
                else:
                    assert mock.get_server_response(response) == response


def test_mock_server_saves_upon_error(tmpdir):
    server = MockServer()
    file_path = os.path.join(tmpdir, 'responses.txt')
    try:
        with server.mock(file_path=file_path, should_save=True) as mock:
            assert mock.get_server_response('response1') == 'response1'
            raise KeyboardInterrupt('exception1')
    except KeyboardInterrupt:
        pass
    new_server = MockServer()
    with new_server.mock_with_file(file_path=file_path) as mock:
        assert mock.get_server_response() == 'response1'
