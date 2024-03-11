"""
locators_and_parsers.py

Defines location handling functions and parsing functions
"""

import json

def get_file_from_vault(vault_path:str, starting_byte:int , ending_byte: int, chunk_size_to_read:int=4096):
    """Efficiently gets raw bytes from vault location on machine

    Args:
        vault_path (str): vault location on disk
        starting_byte (int): file start byte
        ending_byte (int): file end byte
        chunk_size_to_read(int): optional int parameter to determine the amount of chunks to read per file
    """
    with open(vault_path, "rb") as file:
        file_size = ending_byte - starting_byte
        raw_data = b''
        file.seek(starting_byte)
        if file_size > chunk_size_to_read:
            bytes_read = 0
            while bytes_read < file_size:
                chunk_size = min(chunk_size_to_read, file_size - bytes_read)
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                raw_data += chunk
                bytes_read += len(chunk)
        else:
            raw_data = file.read(ending_byte - starting_byte)
    return raw_data

def parse_json_safely(obj:bytes, bgn_magic_len:int , end_magic_len:int) -> dict:
    """Parses the bytes representing a JSON. The JSON must also include the MAGIC bytes

    Args:
        obj (bytes): bytes representing the FULL JSON
        bgn_magic_len (int): length of the magic start bytes
        end_magic_len (int): length of the magic end bytes

    Returns:
        dict: JSON without MAGIC bytes
    """
    try:
        parsed_json = json.loads(obj)
        return parsed_json
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        return {"error": str(e), "json": obj}
