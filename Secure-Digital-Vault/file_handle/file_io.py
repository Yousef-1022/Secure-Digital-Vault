from custom_exceptions.classes_exceptions import FileError
from utils.validators import is_location_ok

import time, json


def get_file_size(file_path : str) -> tuple[int , str]:
    """Gets the file size of the given file_path

    Args:
        file_path (str): File location on the disk

    Returns:
        tuple[int , str]: tuple , where first value represents the size, second value is for any errors.
    """
    result = is_location_ok(file_path, for_file_save=False, for_file_update=True)
    if not result[0]:
        return -1 , result[1]
    the_size = 0
    try:
        with open (file_path, "rb") as f:
            f.seek(0,2)
            the_size = f.tell()
    except Exception as e:
        return -1 , e
    return the_size, ""

def append_bytes_into_file(file_path : str , the_bytes : bytes, create_file : bool = False, file_name : str = "") -> tuple[bool,str]:
    """Adds the bytes into the given file

    Args:
        file_path (str): File location on the disk
        the_bytes (bytes): Bytes which are already encrypted and serialized
        create_file (bool): Optional bool which is by default False, it creates the file if necessary.
        file_name (str) : Option str which is the file name. Used with creat_file

    Returns:
        tuple[bool,str]: First value represents True upon success, False otherwise. Second value is if any error raised.
    """
    if create_file:
        result = is_location_ok(file_path, for_file_save=create_file, for_file_update=False)
    else:
        result = is_location_ok(file_path, for_file_save=create_file, for_file_update=True)
    if not result[0]:
        return False , result[1]
    try:
        if create_file:
            with open(f'{file_path}/{file_name}' , "ab") as f:
                f.write(the_bytes)
        else:
            res = get_file_size(file_path)
            if res[0] < 0 :
                raise FileError(res[1])
            init_size = res[0]
            with open(file_path , "ab") as f:
                f.write(the_bytes)

            res = get_file_size(file_path)
            if res[0] - init_size != len(the_bytes):
                raise FileError(f"Old size: {init_size} != New size: {res[0]} - Bytes to append: {len(the_bytes)}. {res[1]}")
        return True, ""
    except FileError as e:
        return False,e
    except Exception as e:
        return False,e
    True,""

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
