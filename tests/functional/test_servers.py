import os
from dataclasses import dataclass

import pytest

from scientistgpt.servers.base_server import ServerCaller


@dataclass
class MockServer(ServerCaller):

    @staticmethod
    def _get_server_response(should_raise=False):
        if should_raise:
            raise ValueError('exception')
        return 'response'


# tests
def test_server_mock_responses():
    server = MockServer()
    with server.mock(old_records=['response1', 'response2']) as mock:
        assert mock.get_server_response() == 'response1'
        assert mock.get_server_response() == 'response2'


def test_server_mock_exception_when_no_responses_left():
    server = MockServer()
    with server.mock(old_records=['response1'], record_more_if_needed=False) as mock:
        assert mock.get_server_response() == 'response1'
        with pytest.raises(AssertionError):
            mock.get_server_response()


def test_server_mock_records_when_runs_out_of_responses():
    server = MockServer()
    with server.mock(old_records=['response1'], record_more_if_needed=True) as mock:
        assert mock.get_server_response() == 'response1'
        assert mock.get_server_response() == 'response'
        assert mock.new_records == ['response']


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
            mock.get_server_response(True)
        assert isinstance(mock.new_records[0], ValueError)


def test_mock_server_save_load_responses_to_file(tmpdir):
    server = MockServer()
    file_path = os.path.join(tmpdir, 'responses.txt')
    with server.mock(file_path=file_path, should_save=True) as mock:
        assert mock.get_server_response() == 'response'
        with pytest.raises(ValueError):
            mock.get_server_response(True)

    new_server = MockServer()
    with new_server.mock_with_file(file_path=file_path) as mock:
        assert mock.get_server_response() == 'response'
        with pytest.raises(ValueError):
            mock.get_server_response()
