import pytest
import os
from unittest import mock
from utils.helpers import is_proper_extension, is_location_ok, get_file_size, count_digits, force_garbage_collect

def test_is_proper_extension():
    assert is_proper_extension(".json", "json") == True
    assert is_proper_extension(".txt", "txt") == True
    assert is_proper_extension(".txt", "json") == False
    assert is_proper_extension("json") == False
    assert is_proper_extension(".") == False
    assert is_proper_extension("") == False

@mock.patch("os.path.isfile", return_value=True)
@mock.patch("os.path.getsize", return_value=1024)
def test_get_file_size(mock_getsize, mock_isfile):
    assert get_file_size("dummy_path") == 1024
    mock_isfile.return_value = False
    assert get_file_size("dummy_path") == -1

def test_count_digits():
    assert count_digits(0) == 1
    assert count_digits(12345) == 5
    assert count_digits(-12345) == 5
    assert count_digits(1234567890) == 10

def test_force_garbage_collect():
    before, after = force_garbage_collect()
    assert before >= after
