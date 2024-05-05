import json, time


def formulate_header(vault_name : str , extension : str) -> dict:
    """Creates a full header dictionary

    Args:
        vault_name (str): The Vault Name
        extension (str): The Vault Extension

    Returns:
        dict: Representing the full header
    """
    vault_dict = {
        "vault_name" : vault_name,
        "vault_extension" : extension,
        "header_size" : 0,
        "file_size" : 0,
        "trusted_timestamp" : int(time.time()),
        "amount_of_files" : 0,
        "is_vault_encrypted" : True
    }
    map_dict = {
        "file_ids" : [],
        "directory_ids" : [],
        "voice_note_ids" : [],
        "directories" : {},
        "files" : {},
        "voice_notes" : {}
    }
    final_result = {
        "vault" : vault_dict,
        "map" : map_dict
    }
    tmp = len(json.dumps(final_result))
    final_result["vault"]["header_size"] = tmp
    return final_result

def serialize_dict(the_dict : dict) -> bytes:
    """Serializes the given dictionary into bytes

    Args:
        the_dict (dict): The dictionary

    Returns:
        bytes: Bytes which can be put into a file.
    """
    result = json.dumps(the_dict)
    return result.encode()

def deserialize_dict(bytes_as_dict: bytes) -> dict:
    """Deserializes the given bytes into a dictionary

    Args:
        bytes_as_dict (bytes): The bytes representing a dictionary

    Returns:
        dict: Python dictionary
    """
    return json.loads(bytes_as_dict.decode())
