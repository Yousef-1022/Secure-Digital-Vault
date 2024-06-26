from custom_exceptions.classes_exceptions import InvalidMetaData, MissingKeyInJson
from utils.parsers import parse_size_to_string


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

    def __str__(self) -> str:
        return f"{self.__metadata['name']}.{self.__metadata['type']} , Size: {parse_size_to_string(self.__size)}, Encrypted: {self.__file_encrypted}"

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

    def get_path(self):
        """Gets the path of the file

        Returns:
            int|str: the path of the FIle
        """
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

    def set_path(self, path) -> None:
        """Sets the path of the file

        Args:
            path (int|str): Path to set
        """
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
            "path": int,
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
            "note_id": int
        }

        for key, expected_type in expected_types.items():
            if key not in metadata:
                raise MissingKeyInJson(f"Key: '{key}' is missing from the file metadata")
            if not isinstance(metadata[key], expected_type):
                raise InvalidMetaData(f"Key: '{key}' with data: {metadata[key]} is of type: '{type(metadata[key])}' but should be '{expected_type}'")

    def get_as_dict(self) -> dict:
        """Generates the file as a dict existing in the header

        Returns:
            dict: The dict itself which can be added into the header
        """
        res = {}
        res["id"] = self.__id
        res["size"] = self.__size
        res["loc_start"] = self.__loc_start
        res["loc_end"] = self.__loc_end
        res["checksum"] = self.__checksum
        res["file_encrypted"] = self.__file_encrypted
        res["path"] = self.__path
        res["metadata"] = self.__metadata
        return res
