from utils.constants import *
from utils.locators_and_parsers import parse_json_safely
from custom_exceptions.classes_exceptions import JsonWithInvalidData
from custom_exceptions.classes_exceptions import MissingKeyInJson

class Vault:
    def __init__(self, vault_path:str):
        self.__header = {}
        self.__map = {}
        self.__footer = {}
        self.__vault_path = vault_path

    # Getters, Setters and Loaders
    def get_header(self) -> dict:
        return self.__header

    def refresh_header(self, header:dict):
        self.__header = header

    def get_map(self) -> dict:
        return self.__map

    def refresh_map(self, map:dict):
        self.__map = map

    def get_footer(self) -> dict:
        return self.__footer

    def refresh_footer(self, footer:dict):
        self.__footer = footer

    def get_vault_path (self) -> str:
        return self.__vault_path

    def load_into_memory(self):
        pass

    # Header and Footer Validators
    def validate_header(self, full_header:bytes) -> dict:
        """Validates the full header represented in bytes (magic bytes included)

        Args:
            full_header (bytes): Full header representation in bytes

        Raises:
            JsonWithInvalidData: Incase the header contains invalid data
            MissingKeyInJson: Incase there is a missing key within the inner values of the header

        Returns:
            dict: the header without magic bytes
        """
        magic_bgn = full_header[:len(MAGIC_HEADER_START)]
        magic_end = full_header[-len(MAGIC_HEADER_END):]
        if (magic_bgn == MAGIC_HEADER_START) and (magic_end == MAGIC_HEADER_END):
            header = parse_json_safely(full_header, len(MAGIC_HEADER_START), len(MAGIC_HEADER_END))
            if("error" in header):
                raise JsonWithInvalidData(str(header))
            if (self.__check_header_keys(header)):  # Can raise MissingKeyInJson TODO use logger
                return header
        raise JsonWithInvalidData(f"JSON has incorrect magic bytes. Obj len: {len(full_header)}, Obj: {str(full_header)}")

    def __check_header_keys(self, header:dict) -> bool:
        for key in ["vault","map"]:
            if key not in header:
                raise MissingKeyInJson(f"Key: {key} is missing from the Vault main header.")

        for key in VAULT_KEYS:
            if key not in header["vault"]:
                raise MissingKeyInJson(f"Key: {key} is missing from the Vault header.")

        for key in MAP_KEYS:
            if key not in header["map"]:
                raise MissingKeyInJson(f"Key: {key} is missing from the Vault map header.")
        return True

    def validate_footer(self, full_footer:bytes) -> dict:
        """Validates the full footer represented in bytes (magic bytes included)

        Args:
            full_footer (bytes): Full footer representation in bytes

        Raises:
            JsonWithInvalidData: Incase the footer contains invalid data
            MissingKeyInJson: Incase there is a missing key within the inner values of the footer

        Returns:
            dict: the footer without magic bytes
        """
        magic_bgn = full_footer[:len(MAGIC_FOOTER_START)]
        magic_end = full_footer[-len(MAGIC_FOOTER_END):]
        if (magic_bgn == MAGIC_FOOTER_START) and (magic_end == MAGIC_FOOTER_END):
            footer = parse_json_safely(full_footer, len(MAGIC_FOOTER_START), len(MAGIC_FOOTER_END))
            if("error" in footer):
                raise JsonWithInvalidData(str(footer))
            if (self.__check_footer_keys(footer)): # Can raise MissingKeyInJson TODO use logger
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
