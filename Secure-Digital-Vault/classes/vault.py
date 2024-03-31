from utils.constants import *
from utils.parsers import parse_json_safely
from custom_exceptions.classes_exceptions import JsonWithInvalidData, MissingKeyInJson

class Vault:
    def __init__(self, vault_path : str):
        self.__header = {}
        self.__map = {}
        self.__footer = {}
        self.__vault_path = vault_path

    # Getters, Setters and Loaders
    def get_header(self) -> dict:
        return self.__header

    def refresh_header(self, header:dict):
        """Sets the header

        Args:
            header (dict): header to set
        """
        self.__header = header
        self.__map = self.__header["map"]

    def get_map(self) -> dict:
        return self.__map

    def refresh_map(self, map:dict):
        """Sets the map

        Args:
            map (dict): map to set
        """
        self.__map = map

    def get_footer(self) -> dict:
        return self.__footer

    def refresh_footer(self, footer:dict):
        """Sets the footers

        Args:
            footer (dict): footer to set
        """
        self.__footer = footer

    def get_vault_path (self) -> str:
        return self.__vault_path

    def load_into_memory(self):
        pass

    # Header Validators
    def validate_header(self, full_header:bytes) -> dict:
        """Validates the full header represented in bytes

        Args:
            full_header (bytes): Full header representation in bytes

        Raises:
            JsonWithInvalidData: Incase the header contains invalid data
            MissingKeyInJson: Incase there is a missing key within the inner values of the header

        Returns:
            dict: the header without magic bytes
        """
        header = parse_json_safely(full_header)
        if("error" in header):
            raise JsonWithInvalidData(str(header["error"]))
        if (self.__validate_header_keys(header)): # Can raise MissingKeyInJson or JsonWithInvalidData
            return header
        raise JsonWithInvalidData(f"JSON has incorrect magic bytes. Obj len: {len(full_header)}, Obj: {str(full_header)}")

    def __validate_header_keys(self, header: dict) -> bool:
        """Validates the full header of the vault. (vault + map)

        Args:
            header (dict): the whole header containing all keys

        Raises:
            MissingKeyInJson: Indicating that a key does not exist
            JsonWithInvalidData: Indicating that a value is of incorrect type

        Returns:
            bool: Upon success
        """
        for key in ["vault", "map"]:
            if key not in header:
                raise MissingKeyInJson(f"Key '{key}' is missing from the Vault main header.")

        self.__validate_vault_keys(header["vault"])
        self.__validate_map_keys(header["map"])

        return True

    def __validate_vault_keys(self, vault : dict) -> None:
        """Checks if the key 'vault' contains valid keys.

        Args:
            vault (dict): the dict of the the 'vault' key
        """
        for key in VAULT_KEYS:
            if key not in vault:
                raise MissingKeyInJson(f"Key '{key}' is missing from the 'vault' header.")
            if key == "vault_name" or key == "vault_extension":
                try:
                    if not isinstance(vault[key], str):
                        raise JsonWithInvalidData(f"Value for key '{key}' must be a string but '{vault[key]}' is of type: {type(vault[key])}.")
                except KeyError:
                        raise MissingKeyInJson(f"Key '{key}' does not exist in the 'vault' dict!")
            elif key == "is_vault_encrypted":
                try:
                    if not isinstance(vault[key], bool):
                        raise JsonWithInvalidData(f"Value for key 'is_vault_encrypted' must be a boolean but '{vault[key]}' is of type: {type(vault[key])}.")
                except KeyError:
                    raise MissingKeyInJson("Key 'is_vault_encrypted' does not exist in the 'vault' dict!")
            else:
                try:
                    if not isinstance(vault[key], int):
                        raise JsonWithInvalidData(f"Value for key '{key}' must be an integer but '{vault[key]}' is of type: {type(vault[key])}.")
                except KeyError:
                    raise MissingKeyInJson(f"Key '{key}' does not exist in the 'vault' dict!")

    def __validate_map_keys(self, map : dict) -> None:
        """Checks if the key 'map' contains valid keys, but does not check the correctness of files, directories, voice_notes

        Args:
            map (dict): the dict of the the 'map' key
        """
        for key in MAP_KEYS:
            if key not in map:
                raise MissingKeyInJson(f"Key '{key}' is missing from the 'map' dict")
            # file_ids , directory_ids, voice_note_ids
            if key[-3:] == "ids":
                try:
                    if not isinstance(map[key], list):
                        raise JsonWithInvalidData(f"Value for key '{key}' must be a list but '{map[key]}' is of type: {type(map[key])}.")
                    else:
                        for value in map[key]:
                            if not isinstance(value, int):
                                raise JsonWithInvalidData(f"The'{key}' must contain a list of integers but '{value}' is of type: {type(value)}.")
                except KeyError:
                        raise MissingKeyInJson(f"Key '{key}' does not exist in the 'map' dict!")
            # files, directories, voice_notes
            else:
                try:
                    if not isinstance(map[key], list):
                        raise JsonWithInvalidData(f"Value for key '{key}' must be a dict but '{map[key]}' is of type: {type(map[key])}.")
                    else:
                        for value in map[key]:
                            if not isinstance(value, dict):
                                raise JsonWithInvalidData(f"The '{key}' key must contain a list of dict but '{value}' is of type: {type(value)}.")
                except KeyError:
                    raise MissingKeyInJson(f"Key '{key}' does not exist in the 'map' dict!")

    # Footer Validators _ TODO
    def validate_footer(self, full_footer:bytes) -> dict:
        """Validates the full footer represented in bytes

        Args:
            full_footer (bytes): Full footer representation in bytes

        Raises:
            JsonWithInvalidData: Incase the footer contains invalid data
            MissingKeyInJson: Incase there is a missing key within the inner values of the footer

        Returns:
            dict: the footer without magic bytes
        """
        footer = parse_json_safely(full_footer)
        if("error" in footer):
            raise JsonWithInvalidData(str(footer))
        if (self.__check_footer_keys(footer)): # Can raise MissingKeyInJson
            return footer
        raise JsonWithInvalidData(f"JSON has incorrect magic bytes. Obj len: {len(full_footer)}, Obj: {str(full_footer)}")

    def __check_footer_keys(self, footer:dict) -> bool:
        for key in ["error_log", "session_log"]:
            if key not in footer:
                raise MissingKeyInJson(f"Key: {key} is missing from the Vault main Footer.")
            if "loc_start" not in footer[key]:
                raise MissingKeyInJson(f"Key: {key} is missing from the Vault Footer.")
            if "loc_end" not in footer[key]:
                raise MissingKeyInJson(f"Key: {key} is missing from the Vault Footer.")
        return True
