from utils.parsers import parse_size_to_string
from custom_exceptions.classes_exceptions import MissingKeyInJson, JsonWithInvalidData

class Note:
    """Note structure used internally to represent a note within the vault
    """
    def __init__(self, note_info : dict):
        self.validate_mapped_data(note_info)
        self.__id        = note_info["id"]
        self.__owned_by  = note_info["owned_by_file"]
        self.__loc_start = note_info["loc_start"]
        self.__loc_end   = note_info["loc_end"]
        self.__type      = note_info["type"]
        self.__checksum  = note_info["checksum"]

    def __str__(self) -> str:
        return f"Note of type: {self.__type}, Size: {parse_size_to_string(self.__loc_end-self.__loc_start)}"

    def get_id(self) -> int:
        return self.__id

    def set_id(self, the_id : int) -> None:
        self.__id = the_id

    def get_owned_by(self) -> int:
        return self.__owned_by

    def set_owned_by(self, file_id : int) -> None:
        self.__owned_by = file_id

    def get_loc_start(self) -> int:
        return self.__loc_start

    def set_loc_start(self, loc_start : int) -> None:
        self.__loc_start = loc_start

    def get_loc_end(self) -> int:
        return self.__loc_end

    def set_loc_end(self, loc_end:int) -> None:
        self.__loc_end = loc_end

    def get_type(self) -> str:
        return self.__type

    def set_type(self, type : str) -> None:
        self.__type = type

    def get_checksum(self) -> str:
        return self.__checksum

    def set_checksum(self, checksum : str) -> None:
        self.__checksum = checksum

    def get_as_dict(self) -> dict:
        """Returns a dict in the map format

        Returns:
            dict: The dict to add into the map
        """
        return {
            "id" : self.__id,
            "owned_by_file" : self.__owned_by,
            "loc_start" : self.__loc_start,
            "loc_end" : self.__loc_end,
            "type" : self.__type,
            "checksum" : self.__checksum
        }

    def validate_mapped_data(self, data : dict) -> None:
        """Checks whether the passed dict represents a valid Dictionary

        Args:
            data_dict (dict): dict from the dictionaries map

        """
        expected_types = {
            "id": int,
            "owned_by_file": int,
            "loc_start": int,
            "loc_end": int,
            "type": str,
            "checksum": str
        }

        for key, expected_type in expected_types.items():
            if key not in data:
                raise MissingKeyInJson(f"Key: '{key}' is missing from the dict map data")
            if not isinstance(data[key], expected_type):
                raise JsonWithInvalidData(f"Key: '{key}' with data: '{data[key]}' should be of type {expected_type} but is of type: '{type(data[key])}'")
