from custom_exceptions.classes_exceptions import InvalidMetaData, MissingKeyInJson

class File:
    """File structure used internally to represent a file within the vault
    """
    def __init__(self, file_info:dict):
        self.validate_mapped_data(file_info)
        self.__id             = file_info["id"]
        self.__size           = file_info["size"]
        self.__loc_start      = file_info["loc_start"]
        self.__loc_end        = file_info["loc_end"]
        self.__checksum       = file_info["checksum"]
        self.__file_encrypted = file_info["file_encrypted"]
        self.__path           = file_info["path"]
        self.__metadata       = file_info["metadata"]

    def __str__(self):
        if ({self.__metadata["name"]} and {self.__metadata["type"]}):
            return f'File: {self.__path}{self.__metadata["name"]}{self.__metadata["type"]}, id:{self.__id}'
        return f"File: {self.__path}, id:{self.__id}"

    # Getter methods
    def get_id(self) -> int:
        return self.__id

    def get_size(self) -> int:
        return self.__size

    def get_loc_start(self) -> int:
        return self.__loc_start

    def get_loc_end(self) -> int:
        return self.__loc_end

    def get_checksum(self) -> str:
        return self.__checksum

    def get_file_encrypted(self) -> bool:
        return self.__file_encrypted

    def get_path(self) -> str:
        return self.__path

    def get_metadata(self) -> dict:
        return self.__metadata

    # Setter methods
    def set_id(self, id:int) -> None:
        self.__id = id

    def set_size(self, size:int) -> None:
        self.__size = size

    def set_loc_start(self, loc_start:int) -> None:
        self.__loc_start = loc_start

    def set_loc_end(self, loc_end:int) -> None:
        self.__loc_end = loc_end

    def set_checksum(self, checksum:str) -> None:
        self.__checksum = checksum

    def set_file_encrypted(self, file_encrypted:bool) -> None:
        self.__file_encrypted = file_encrypted

    def set_path(self, path:str) -> None:
        self.__path = path

    def set_metadata(self, metadata:dict) -> None:
        self.__metadata = metadata

    def validate_mapped_data(self, data:dict) -> None:
        """Checks whether all the keys in the data dict are valid, including the metadata.

        Args:
            data (dict): data dict with all the values
        """
        expected_types = {
            "id": int,
            "size": int,
            "loc_start": int,
            "loc_end": int,
            "checksum": str,
            "file_encrypted": bool,
            "path": str,
            "metadata" : dict,
        }

        for key, expected_type in expected_types.items():
            if key not in data:
                raise MissingKeyInJson(f"Key: '{key}' is missing from the file map data")
            if not isinstance(data[key], expected_type):
                raise InvalidMetaData(f"Key: '{key}' with data: {data[key]} is of type: '{type(data[key])}' but should be '{expected_type}'")
        self.validate_metadata(data["metadata"])

    def validate_metadata(self, metadata: dict) -> None:
        """Checks whether all the keys in the metadata dict are valid

        Args:
            metadata (dict): metadata dict with all the values
        """
        expected_types = {
            "name": str,
            "type": str,
            "data_created": int,
            "last_modified": int,
            "icon_data_start": int,
            "icon_data_end": int,
            "voice_note_id": int
        }

        for key, expected_type in expected_types.items():
            if key not in metadata:
                raise MissingKeyInJson(f"Key: '{key}' is missing from the file metadata")
            if not isinstance(metadata[key], expected_type):
                raise InvalidMetaData(f"Key: '{key}' with data: {metadata[key]} is of type: '{type(metadata[key])}' but should be '{expected_type}'")

