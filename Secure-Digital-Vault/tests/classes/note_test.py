import pytest
from custom_exceptions.classes_exceptions import MissingKeyInJson, JsonWithInvalidData
from utils.parsers import parse_size_to_string
from classes.note import Note

@pytest.fixture
def valid_note_info():
    return {
        "id": 1,
        "owned_by_file": 1,
        "loc_start": 0,
        "loc_end": 100,
        "type": "text",
        "checksum": "abc123"
    }

@pytest.fixture
def note(valid_note_info):
    return Note(valid_note_info)

def test_initialization(note, valid_note_info):
    assert note.get_id() == valid_note_info["id"]
    assert note.get_owned_by() == valid_note_info["owned_by_file"]
    assert note.get_loc_start() == valid_note_info["loc_start"]
    assert note.get_loc_end() == valid_note_info["loc_end"]
    assert note.get_type() == valid_note_info["type"]
    assert note.get_checksum() == valid_note_info["checksum"]

def test_str(note, valid_note_info):
    expected_str = f"Note of type: {valid_note_info['type']}, Size: {parse_size_to_string(valid_note_info['loc_end'] - valid_note_info['loc_start'])}"
    assert str(note) == expected_str

def test_getters_and_setters(note):
    note.set_id(2)
    assert note.get_id() == 2

    note.set_owned_by(2)
    assert note.get_owned_by() == 2

    note.set_loc_start(50)
    assert note.get_loc_start() == 50

    note.set_loc_end(150)
    assert note.get_loc_end() == 150

    note.set_type("markdown")
    assert note.get_type() == "markdown"

    note.set_checksum("def456")
    assert note.get_checksum() == "def456"

def test_validate_mapped_data():
    valid_data = {
        "id": 1,
        "owned_by_file": 1,
        "loc_start": 0,
        "loc_end": 100,
        "type": "text",
        "checksum": "abc123"
    }

    invalid_data_missing_key = valid_data.copy()
    invalid_data_missing_key.pop("id")

    invalid_data_wrong_type = valid_data.copy()
    invalid_data_wrong_type["loc_start"] = "not an int"

    with pytest.raises(MissingKeyInJson):
        Note(invalid_data_missing_key)

    with pytest.raises(JsonWithInvalidData):
        Note(invalid_data_wrong_type)

def test_get_as_dict(note, valid_note_info):
    assert note.get_as_dict() == valid_note_info
