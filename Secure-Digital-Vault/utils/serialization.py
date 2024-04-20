from utils.constants import MAGIC_HEADER_START , MAGIC_HEADER_END
from crypto.utils import xor_magic

import json

def serialize_dict(the_dict : dict) -> bytes:
    """Serializes the given dictionary into bytes

    Args:
        the_dict (dict): The dictionary

    Returns:
        bytes: Bytes which can be put into a file.
    """
    result = json.dumps(the_dict)
    return result.encode()

import json

def deserialize_dict(bytes_as_dict: bytes) -> dict:
    """Deserializes the given bytes into a dictionary

    Args:
        bytes_as_dict (bytes): The bytes representing a dictionary

    Returns:
        dict: Python dictionary
    """
    return json.loads(bytes_as_dict.decode())

def add_magic_into_header(bytes_as_dict : bytes) -> bytes:
    """Adds the relevant magic bytes into the serialized and encrypted dict

    Args:
        bytes_as_dict (bytes): Serialized and Encrypted dict

    Returns:
        bytes: Same bytes but with the magic bytes at front and back.
    """
    return bytes(xor_magic(MAGIC_HEADER_START) + bytes_as_dict + xor_magic(MAGIC_HEADER_END))
