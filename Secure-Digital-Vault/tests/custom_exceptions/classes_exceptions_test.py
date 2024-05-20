import pytest
from custom_exceptions.classes_exceptions import (
    FileDoesNotExist,
    JsonWithInvalidData,
    MissingKeyInJson,
    InvalidMetaData,
    FileError,
    DecryptionFailure,
    EncryptionFailure,
)

def test_FileDoesNotExist():
    with pytest.raises(FileDoesNotExist) as exc_info:
        raise FileDoesNotExist("File not found")
    assert str(exc_info.value) == "FileDoesNotExist exception raised. File not found"

def test_JsonWithInvalidData():
    with pytest.raises(JsonWithInvalidData) as exc_info:
        raise JsonWithInvalidData("Invalid JSON data")
    assert str(exc_info.value) == "JsonWithInvalidData: Invalid JSON data"

def test_MissingKeyInJson():
    with pytest.raises(MissingKeyInJson) as exc_info:
        raise MissingKeyInJson("Missing key in JSON")
    assert str(exc_info.value) == "MissingKeyInJson: Missing key in JSON"

def test_InvalidMetaData():
    with pytest.raises(InvalidMetaData) as exc_info:
        raise InvalidMetaData("Invalid metadata")
    assert str(exc_info.value) == "InvalidMetaData: Invalid metadata"

def test_FileError():
    with pytest.raises(FileError) as exc_info:
        raise FileError("Error while processing file")
    assert str(exc_info.value) == "FileError: Error while processing file"

def test_DecryptionFailure():
    with pytest.raises(DecryptionFailure) as exc_info:
        raise DecryptionFailure("Failed to decrypt")
    assert str(exc_info.value) == "DecryptionFailure: Failed to decrypt"

def test_EncryptionFailure():
    with pytest.raises(EncryptionFailure) as exc_info:
        raise EncryptionFailure("Failed to encrypt")
    assert str(exc_info.value) == "EncryptionFailure: Failed to encrypt"
