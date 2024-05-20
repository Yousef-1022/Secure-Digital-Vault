import pytest
from classes.directory import Directory
from custom_exceptions.classes_exceptions import FileDoesNotExist, MissingKeyInJson, JsonWithInvalidData
from classes.file import File

@pytest.fixture
def valid_data_dict():
    return {
        "id": 1,
        "name": "Test Directory",
        "path": 0,
        "data_created": 1234567890,
        "last_modified": 1234567890,
        "files": []
    }

@pytest.fixture
def directory(valid_data_dict):
    return Directory(valid_data_dict)

def test_initialization(directory, valid_data_dict):
    assert directory.get_id() == valid_data_dict["id"]
    assert directory.get_name() == valid_data_dict["name"]
    assert directory.get_path() == valid_data_dict["path"]
    assert directory.get_data_created() == valid_data_dict["data_created"]
    assert directory.get_last_modified() == valid_data_dict["last_modified"]
    assert directory.get_files() == valid_data_dict["files"]

def test_str(directory):
    assert str(directory) == "Test Directory , Total of files excluding subfolders: 0"

def test_setters_and_getters(directory):
    directory.set_id(2)
    assert directory.get_id() == 2

    directory.set_name("New Name")
    assert directory.get_name() == "New Name"

    directory.set_path(10)
    assert directory.get_path() == 10

    new_date = 987654321
    directory.set_last_modified(new_date)
    assert directory.get_last_modified() == new_date

def test_get_metadata(directory):
    metadata = directory.get_metadata()
    assert metadata == {
        "name": "Test Directory",
        "type": "Folder",
        "data_created": 1234567890,
        "last_modified": 1234567890,
        "files": 0
    }

def test_get_as_dict(directory, valid_data_dict):
    assert directory.get_as_dict() == valid_data_dict

def test_validate_mapped_data():

    invalid_data_missing_key = {
        "id": 1,
        "name": "Test Directory",
        "path": 0,
        "data_created": 1234567890,
        "last_modified": 1234567890
        # Missing 'files'
    }

    invalid_data_wrong_type = {
        "id": 1,
        "name": "Test Directory",
        "path": 0,
        "data_created": 1234567890,
        "last_modified": 1234567890,
        "files": "not a list"
    }

    with pytest.raises(MissingKeyInJson):
        Directory(invalid_data_missing_key)

    with pytest.raises(JsonWithInvalidData):
        Directory(invalid_data_wrong_type)

def test_determine_parent_by_id():
    data_dict = {
        1: {"id": 1, "path": 0},
        2: {"id": 2, "path": 1}
    }

    assert Directory.determine_parent_by_id(2, data_dict) == 1
    assert Directory.determine_parent_by_id(1, data_dict) == 0
    assert Directory.determine_parent_by_id(3, data_dict) == 0

def test_add_file(directory):
    file = File({
                "id" : 2,
                "size" : 1024,
                "loc_start" : 2000,
                "loc_end" : 3024,
                "checksum" : "0x6cxf9dd",
                "file_encrypted" : False,
                "path" : 1,
                "metadata" : {
                    "name" : "Graves & Jupe - VHS",
                    "type" : ".mp3",
                    "data_created" : 1710081055,
                    "last_modified" : 1710081069,
                    "icon_data_start": 3665,
                    "icon_data_end" : 15498,
                    "note_id" : -1
                }
            })
    assert directory.add_file(file) is True
    assert directory.get_files() == [file]
    assert directory.add_file(file) is False

def test_remove_file(directory):
    file = File({
                "id" : 2,
                "size" : 1024,
                "loc_start" : 2000,
                "loc_end" : 3024,
                "checksum" : "0x6cxf9dd",
                "file_encrypted" : False,
                "path" : 1,
                "metadata" : {
                    "name" : "Graves & Jupe - VHS",
                    "type" : ".mp3",
                    "data_created" : 1710081055,
                    "last_modified" : 1710081069,
                    "icon_data_start": 3665,
                    "icon_data_end" : 15498,
                    "note_id" : -1
                }
            })
    directory.add_file(file)

    assert directory.remove_file(file) is True
    assert directory.get_files() == []

    with pytest.raises(FileDoesNotExist):
        directory.remove_file(file)
