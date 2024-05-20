import pytest
import json
from utils.serialization import formulate_header, formulate_footer, serialize_dict, deserialize_dict

def test_formulate_header():
    vault_name = "TestVault"
    extension = ".vault"
    result = formulate_header(vault_name, extension)
    assert isinstance(result, dict)
    assert result["vault"]["vault_name"] == vault_name
    assert result["vault"]["vault_extension"] == extension
    assert result["vault"]["header_size"] > 0
    assert result["vault"]["file_size"] == 0
    assert result["vault"]["amount_of_files"] == 0
    assert result["vault"]["is_vault_encrypted"] == True
    assert isinstance(result["map"], dict)
    assert result["map"]["file_ids"] == []
    assert result["map"]["directory_ids"] == []
    assert result["map"]["note_ids"] == []
    assert result["map"]["directories"] == {}
    assert result["map"]["files"] == {}
    assert result["map"]["notes"] == {}

def test_formulate_footer():
    result = formulate_footer()
    assert isinstance(result, dict)
    assert result["error_log"] == ""
    assert result["session_log"] == ""

def test_serialize_dict():
    test_dict = {"key": "value"}
    result = serialize_dict(test_dict)
    assert isinstance(result, bytes)
    assert result == json.dumps(test_dict).encode()

def test_deserialize_dict():
    test_dict = {"key": "value"}
    bytes_dict = serialize_dict(test_dict)
    result = deserialize_dict(bytes_dict)
    assert isinstance(result, dict)
    assert result == test_dict
