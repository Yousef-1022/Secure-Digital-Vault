import pytest
from classes.vault import Vault
from utils.serialization import serialize_dict
from custom_exceptions.classes_exceptions import JsonWithInvalidData, MissingKeyInJson

def test_vault_initialization():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    assert vault.get_password() == "password123"
    assert vault.get_vault_path() == "/path/to/vault"
    assert vault.get_hint() == "No Hint"
    assert vault.get_header() == {}
    assert vault.get_footer() == {"error_log": "", "session_log": ""}
    assert vault.get_map() == {}

def test_set_and_get_header():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    header = {"vault": {"header_size": 128}, "map": {}}
    vault.set_header(header)
    assert vault.get_header() == header

def test_set_and_get_footer():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    footer = {"error_log": "Error", "session_log": "Session"}
    vault.set_footer(footer)
    assert vault.get_footer() == footer

def test_add_error_log_to_footer():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    vault.add_error_log_to_footer("Error1")
    assert vault.get_footer()["error_log"] == "Error1"

def test_add_normal_log_to_footer():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    vault.add_normal_log_to_footer("Log1")
    assert vault.get_footer()["session_log"] == "Log1"

def test_refresh_header():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    header = {"vault": {"header_size": 10}, "map": {}}
    vault.set_header(header)
    refreshed_header = vault.refresh_header(return_it=True)
    assert "vault" in refreshed_header.decode()
    assert "map" in refreshed_header.decode()

def test_set_and_get_password():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    vault.set_password("newpassword123")
    assert vault.get_password() == "newpassword123"

def test_set_and_get_hint():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    vault.set_hint("New Hint")
    assert vault.get_hint() == "New Hint"

def test_determine_if_dir_path_is_valid():
    vault = Vault(password="password123", vault_path="/path/to/vault")

    dir1 = {
        "id": 1,
        "name": "path",
        "path": 0,
        "data_created": 1234567890,
        "last_modified": 1234567890,
        "files": []
    }

    dir2 = {
        "id": 2,
        "name": "to",
        "path": 1,
        "data_created": 1234567890,
        "last_modified": 1234567890,
        "files": []
    }

    dir3 = {
        "id": 3,
        "name": "path",
        "path": 2,
        "data_created": 1234567890,
        "last_modified": 1234567890,
        "files": []
    }

    dir4 = {
        "id": 4,
        "name": "somewhere",
        "path": 2,
        "data_created": 1234567890,
        "last_modified": 1234567890,
        "files": []
    }
    vault.set_map({
        "files" : {},
        "directories" : {}
    })
    vault.get_map()["directories"]["1"] = dir1
    vault.get_map()["directories"]["2"] = dir2
    vault.get_map()["directories"]["3"] = dir3
    assert vault.determine_if_dir_path_is_valid(["path","to","somewhere"]) == (False, 2)
    vault.get_map()["directories"]["4"] = dir4
    assert vault.determine_if_dir_path_is_valid(["path","to","somewhere"]) == (True, 4)
    assert vault.determine_if_dir_path_is_valid(["path","to","NO"]) == (False, 2)

def test_determine_directory_path():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    data_dict = {"1": {"name": "folder1", "path": 0}, "2": {"name": "folder2", "path": 1}}
    assert Vault.determine_directory_path(2, data_dict) == "/folder1/folder2/"

def test_generate_id():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    vault.set_map({"file_ids": [], "directory_ids": [], "note_ids": []})
    file_id = vault.generate_id("F")
    assert file_id in vault.get_map()["file_ids"]

def test_get_id_from_vault():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    vault.set_map({"file_ids": [1], "files": {"1": {"id": 1, "name": "file1"}}})
    exists, file = vault.get_id_from_vault(1, "F")
    assert exists is True
    assert file["name"] == "file1"

def test_get_name_of_id():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    vault.set_map({"file_ids": [1], "files": {"1": {"id": 1, "metadata": {"name": "file1"}}}})
    assert vault.get_name_of_id(1, "F") == "file1"

def test_validate_header():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    valid_header = {
        "vault": {
            "vault_name" : "Vault",
            "vault_extension" : ".vault",
            "header_size" : 512,
            "file_size" : 2816,
            "trusted_timestamp" : 1710070050,
            "amount_of_files" : 69,
            "is_vault_encrypted" : True
        },
        "map": {
            "file_ids" : [],
            "directory_ids" : [],
            "note_ids" : [],
            "directories" : {},
            "files" : {},
            "notes" : {}
        }
    }
    as_bytes = serialize_dict(valid_header)
    assert vault.validate_header(as_bytes) == valid_header

    invalid_header = b'{"vault": {"header_size": "ten"}, "map": {}}'
    with pytest.raises(MissingKeyInJson):
        vault.validate_header(invalid_header)

    with pytest.raises(JsonWithInvalidData):
        vault.validate_header(b'xxx')

def test_validate_footer():
    vault = Vault(password="password123", vault_path="/path/to/vault")
    valid_footer = b'{"error_log": "", "session_log": ""}'
    assert vault.validate_footer(valid_footer) == {"error_log": "", "session_log": ""}

    invalid_footer = b'{"error_log": ""}'
    with pytest.raises(MissingKeyInJson):
        vault.validate_footer(invalid_footer)
