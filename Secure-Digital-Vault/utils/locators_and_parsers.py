"""
locators_and_parsers.py

Defines location handling functions and parsing functions
"""

import json, os, string

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
    except (json.JSONDecodeError, TypeError, ValueError, Exception) as e:
        msg = f"ExceptionType: {type(e).__name__}. Message: {str(e)}"
        return {"error": msg, "json": obj}

def parse_size_to_string(amount_bytes: int) -> str:
    """
    Convert the given amount of bytes to a human-readable string representing the size.

    Args:
        amount_bytes (int): The amount of bytes.

    Returns:
        str: A string representing the size.
    """
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    index = 0
    while amount_bytes >= 1024 and index < len(suffixes) - 1:
        amount_bytes /= 1024.0
        index += 1
    return '{:.2f} {}'.format(amount_bytes, suffixes[index])

def parse_from_string_to_size(size_instr: str) -> int:
    """
    Convert the given string representing a size to an integer amount of bytes.

    Args:
        size_instr (str): The string representing the size.

    Returns:
        int: The amount of bytes.
    """
    size_instr = size_instr.strip().upper()
    suffixes = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4
    }
    for suffix, factor in suffixes.items():
        if size_instr.endswith(suffix):
            size_value = size_instr[:-len(suffix)].strip()
            try:
                return int(float(size_value) * factor)
            except ValueError as e:
                print(e)
                return -1  # Unable to parse
    return -1  # Unknown suffix


def get_available_drives() -> list[str]:
    """Returns a list of available drives in the system.

    Returns:
        list: A list of available drives with backslash, e.g., ['C:\\\\', 'D:\\\\', 'E:\\\\'].
    """
    drives = []
    if os.name == 'nt':  # For Windows
        for letter in string.ascii_uppercase:
            drive = letter + ':\\'
            if os.path.exists(drive):
                drives.append(drive)
    return drives