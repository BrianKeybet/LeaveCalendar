from io import StringIO
from datetime import datetime
import pytest
from tasks import open_log_file, close_log_file, get_mysql_connection
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Connection
from decouple import config
from sqlalchemy.testing import mock

# Define a fixture to create a temporary log file
@pytest.fixture
def temporary_log_file():
    log_file = StringIO()
    # log_file.getvalue = log_file.read
    yield log_file
    log_file.close()

# Define a fixture to mock the log_file
@pytest.fixture
def mock_log_file():
    class MockLogFile:
        def write(self, message):
            self.logged_message = message
    return MockLogFile()

# Mocking the config function
@pytest.fixture
def mock_config(monkeypatch):
    def mock_config_function(param):
        if param == 'MYSQL_PASSWORD':
            return config('MYSQL_PASSWORD')
        return None

    monkeypatch.setattr('tasks.config', mock_config_function)

def test_open_log_file():
    log_file = open_log_file()

    assert log_file is not None

def test_close_log_file(temporary_log_file):
    log_file = temporary_log_file
    # Call the close_log_file function with the log file
    close_log_file(log_file)
    assert log_file.closed

def test_get_mysql_connection(mock_log_file, mock_config):
    # Mock the create_engine function and the connection
    with mock.patch('tasks.create_engine') as mock_create_engine:
        with mock.patch('sqlalchemy.engine.Connection') as mock_connection:
            mysql_connection = get_mysql_connection(mock_log_file)

            # Assertions
            assert mock_log_file.logged_message == 'Connecting to MySQL database...\n'

def test_get_mysql_connection_exception(mock_log_file, monkeypatch):
    # Mock the config function to raise an exception
    def mock_config_function(param):
        raise Exception('Configuration error')

    monkeypatch.setattr('tasks.config', mock_config_function)

    # Call the function, which should raise an exception
    with pytest.raises(ValueError):
        get_mysql_connection(mock_log_file)



