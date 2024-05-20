import pytest
import json
from datetime import datetime
from utils.parsers import (
    parse_json_safely, parse_size_to_string, parse_from_string_to_size,
    parse_timestamp_to_string, parse_directory_string, parse_file_name,
    show_as_windows_directory, remove_trailing_slash, get_last_folder
)

def test_parse_json_safely():
    assert parse_json_safely(b'{"key": "value"}') == {"key": "value"}
    assert "error" in parse_json_safely(b'invalid json')
    assert parse_json_safely(b'{"key": "value"}') == {"key": "value"}

def test_parse_size_to_string():
    assert parse_size_to_string(1024) == "1.00 KB"
    assert parse_size_to_string(1048576) == "1.00 MB"
    assert parse_size_to_string(123) == "123.00 B"

def test_parse_from_string_to_size():
    assert parse_from_string_to_size("1 KB") == 1024
    assert parse_from_string_to_size("1 MB") == 1048576
    assert parse_from_string_to_size("1 GB") == 1073741824
    assert parse_from_string_to_size("1.5 GB") == 1610612736
    assert parse_from_string_to_size("invalid size") == -1

def test_parse_timestamp_to_string():
    assert parse_timestamp_to_string(1710050055) == datetime.fromtimestamp(1710050055).strftime("%d-%b-%y %H:%M")

def test_parse_directory_string():
    assert parse_directory_string("/path/to/somewhere/") == (True, ["path", "to", "somewhere"])
    assert parse_directory_string("invalid|path") == (False, [])
    assert parse_directory_string("/") == (True, ["/"])

def test_parse_file_name():
    assert parse_file_name("valid_name") == (True, "")
    assert parse_file_name("invalid:name") == (False, "Name 'invalid:name' contains an invalid character ':'")

def test_show_as_windows_directory():
    assert show_as_windows_directory("D:/path/to/somewhere/") == "D:\\path\\to\\somewhere\\"
    assert show_as_windows_directory("path/to/somewhere/") == "path\\to\\somewhere\\"

def test_remove_trailing_slash():
    assert remove_trailing_slash("path/folder/") == "path/folder"
    assert remove_trailing_slash("path/folder") == "path/folder"
    assert remove_trailing_slash("", add_slash_to_start=True) == "/"
    assert remove_trailing_slash("path/folder/", add_slash_to_start=True) == "/path/folder"

def test_get_last_folder():
    assert get_last_folder("path/to/folder/") == "folder"
    assert get_last_folder("path/to/folder") == "folder"
    assert get_last_folder("/") == "/"
