from custom_exceptions.classes_exceptions import FileError
from math import log10

import os, string


def is_proper_extension(extension : str, type_of_extension : str = None) -> bool:
    """Checks whether the given string is a valid extension.

    Args:
        extension (str): Provided string with the dot, e.g., .json
        type_of_extension (str, optional): Type of extension without the dot which the extension string represents, e.g., json

    Returns:
        bool: True if the extension is proper, False otherwise.
    """
    if extension is None or not extension or extension[0] != "." or len(extension) < 2:
        return False
    if extension.count('.') != 1:
        return False
    if type_of_extension is None or not type_of_extension:
        return True
    return extension[1:] == type_of_extension

def is_location_ok(location_path : str, for_file_save : bool = True, for_file_update : bool = False) -> tuple[bool,str]:
    """Checks whether the given location path is valid.

    Args:
        location_path (str): Provided location path
        for_file_save (bool): Check if its possible to save a file there. True by Default
        for_file_update (bool): Check if its possible to update a file there. False by Default

    Returns:
        tuple[bool,str]: Tuple, first value represents if path is ok , second value represents an error string
    """
    try:
        file_exists = os.path.isfile(location_path)

        if for_file_update:
            if not file_exists:
                raise FileError(f"File: {location_path} does not exist!")
            else:
                with open(location_path, "rb") as f:
                    f.read(1)
                return True , ""

        if for_file_save and file_exists:
            raise FileExistsError(f"File: {location_path} exists! Will not override!")

        is_dir = os.path.isdir(location_path)
        if for_file_save and not is_dir:
            return False, f"Path '{location_path}' is not a Directory! Cannot save a file."

        target = f"{location_path}\\tmp" if location_path[-1] != "/" or location_path[-1] != "\\" else location_path
        target_data = "ok"
        return_val_ok = True

        with open(target,"wb") as f:
            f.write(target_data.encode())
        with open(target,"rb") as f:
            if not f.read().decode() == target_data:
                return_val_ok = False

        if return_val_ok and os.path.exists(target):
            os.remove(target)
        else:
            raise FileError (f"Unknown Error occured when trying to write and delete '{target}'")
        return return_val_ok,""
    except FileExistsError as e:
        return False,e
    except PermissionError as e:
        return False,e
    except FileError as e:
        return False, e
    except Exception as e:
        return False,e

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

def count_digits(number : int) -> int:
    """Counts the number of digits of the given number

    Args:
        number (int): the number

    Returns:
        int: amount of digits
    """
    if number == 0:
        return 1
    digits = int(log10(abs(number))) + 1
    return digits
