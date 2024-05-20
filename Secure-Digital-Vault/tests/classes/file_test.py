import pytest
from custom_exceptions.classes_exceptions import InvalidMetaData, MissingKeyInJson
from utils.parsers import parse_size_to_string
from classes.file import File

@pytest.fixture
def valid_file_info():
    return {
        "id": 1,
        "size": 1024,
        "loc_start": 0,
        "loc_end": 1023,
        "checksum": "abc123",
        "file_encrypted": True,
        "path": 0,
        "metadata": {
            "name": "example",
            "type": "txt",
            "data_created": 1617181920,
            "last_modified": 1617181920,
            "icon_data_start": 10,
            "icon_data_end": 20,
            "note_id": 42
        }
    }

@pytest.fixture
def file(valid_file_info):
    return File(valid_file_info)

def test_initialization(file, valid_file_info):
    assert file.get_id() == valid_file_info["id"]
    assert file.get_size() == valid_file_info["size"]
    assert file.get_loc_start() == valid_file_info["loc_start"]
    assert file.get_loc_end() == valid_file_info["loc_end"]
    assert file.get_checksum() == valid_file_info["checksum"]
    assert file.get_file_encrypted() == valid_file_info["file_encrypted"]
    assert file.get_path() == valid_file_info["path"]
    assert file.get_metadata() == valid_file_info["metadata"]

def test_str(file, valid_file_info):
    expected_str = f"{valid_file_info['metadata']['name']}.{valid_file_info['metadata']['type']} , Size: {parse_size_to_string(valid_file_info['size'])}, Encrypted: {valid_file_info['file_encrypted']}"
    assert str(file) == expected_str

def test_getters_and_setters(file):
    file.set_id(2)
    assert file.get_id() == 2

    file.set_size(2048)
    assert file.get_size() == 2048

    file.set_loc_start(100)
    assert file.get_loc_start() == 100

    file.set_loc_end(2148)
    assert file.get_loc_end() == 2148

    file.set_checksum("def456")
    assert file.get_checksum() == "def456"

    file.set_file_encrypted(False)
    assert file.get_file_encrypted() is False

    file.set_path(1)
    assert file.get_path() == 1

    new_metadata = {
        "name": "new_example",
        "type": "pdf",
        "data_created": 1718192021,
        "last_modified": 1718192021,
        "icon_data_start": 30,
        "icon_data_end": 40,
        "note_id": 43
    }
    file.set_metadata(new_metadata)
    assert file.get_metadata() == new_metadata

def test_validate_mapped_data():
    valid_data = {
        "id": 1,
        "size": 1024,
        "loc_start": 0,
        "loc_end": 1023,
        "checksum": "abc123",
        "file_encrypted": True,
        "path": 0,
        "metadata": {
            "name": "example",
            "type": "txt",
            "data_created": 1617181920,
            "last_modified": 1617181920,
            "icon_data_start": 10,
            "icon_data_end": 20,
            "note_id": 42
        }
    }

    invalid_data_missing_key = valid_data.copy()
    invalid_data_missing_key.pop("id")

    invalid_data_wrong_type = valid_data.copy()
    invalid_data_wrong_type["size"] = "not an int"

    with pytest.raises(MissingKeyInJson):
        File(invalid_data_missing_key)

    with pytest.raises(InvalidMetaData):
        File(invalid_data_wrong_type)

def test_validate_metadata():
    valid_metadata = {
        "name": "example",
        "type": "txt",
        "data_created": 1617181920,
        "last_modified": 1617181920,
        "icon_data_start": 10,
        "icon_data_end": 20,
        "note_id": 42
    }

    invalid_metadata_missing_key = valid_metadata.copy()
    invalid_metadata_missing_key.pop("name")

    invalid_metadata_wrong_type = valid_metadata.copy()
    invalid_metadata_wrong_type["data_created"] = "not an int"

    with pytest.raises(MissingKeyInJson):
        File.validate_metadata(File, invalid_metadata_missing_key)

    with pytest.raises(InvalidMetaData):
        File.validate_metadata(File, invalid_metadata_wrong_type)

def test_get_as_dict(file, valid_file_info):
    assert file.get_as_dict() == valid_file_info
