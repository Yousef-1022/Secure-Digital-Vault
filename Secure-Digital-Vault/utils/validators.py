from custom_exceptions.classes_exceptions import FileError
import os

def is_proper_extension(extension : str, type_of_extension : str = None) -> bool:
    """Checks whether the given string is a valid extension.

    Args:
        extension (str): Provided string with the dot, e.g., .json
        type_of_extension (str, optional): Type of extension without the dot which the extension string represents, e.g., json

    Returns:
        bool: True if the extension is proper, False otherwise.
    """
    if extension is None or not extension or extension[0] != "." or len(extension) < 2:
        #TODO logger
        return False
    if extension.count('.') != 1:
        #TODO logger
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
