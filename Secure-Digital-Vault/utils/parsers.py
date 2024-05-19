import json
from datetime import datetime


def parse_json_safely(obj:bytes) -> dict:
    """Parses the bytes representing a JSON.

    Args:
        obj (bytes): bytes representing the FULL JSON

    Returns:
        dict: JSON, if invalid, the first key is: error
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
                return -1  # Unable to parse
    return -1  # Unknown suffix

def parse_timestamp_to_string(timestamp : int) -> str:
    """Parses a timestamp, e.g, 1710050055 to the string reprsentation: DD-MM-YY 00:00

    Args:
        timestamp (int): Timestamp

    Returns:
        str: reprsentation: DD-MM-YY 00:00
    """
    date_time = datetime.fromtimestamp(timestamp)
    formatted_date_time = date_time.strftime("%d-%b-%y %H:%M")
    return formatted_date_time

def parse_directory_string(dir_path: str) -> tuple[bool, list[str]]:
    """Parses a directory path name, e.g, /path/to/somewhere/

    Args:
        dir (str): Directory path string

    Returns:
        tuple: first part is a boolean if the directory string is a valid path, second is the list of dirs, e.g, [path,to,somewhere]
    """
    forbidden_names = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*", "\0", "."]
    tmp = [dir_name for dir_name in dir_path.split("/") if dir_name != ""]
    len1 = len(tmp)
    if len1 == 0:
        return (True,["/"])
    lst = [e for e in tmp if not any(char in forbidden_names for char in e)]
    len2 = len(lst)
    return (len1 == len2,lst)

def parse_file_name(name : str) -> tuple[bool,str]:
    """Checks whether the given name is suitable for a file name, it cannot contain forbidden characters

    Args:
        name (str): The name

    Returns:
        tuple[bool,str]: First value indicates if its true or false, second value is for error reason if false.
    """
    forbidden_chars = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*", "\0", ".", ","]
    for char in name:
        if char in forbidden_chars:
            return False , f"Name '{name}' contains an invalid character '{char}'"
    return True, ''

def show_as_windows_directory(dir_path : str) -> str:
    """Parses a valid directory path, e.g, D:/path/to/somewhere/ , and returns a windows format style location

    Args:
        dir_path (str): Directory path string without the drive

    Returns:
        str: Parsed Directory as Windows likes, e.g, D:\\path\\to\\somewhere\\
    """
    tmp = dir_path.replace('\\', '/')
    tmp = [folder for folder in tmp.split("/") if folder != '']
    res = '\\'.join(tmp) + '\\'
    return res

def remove_trailing_slash(path : str,  add_slash_to_start : bool = False) -> str:
    """Removes the trailing slash if possible, e.g, path/folder/ returns path/folder

    Args:
        path (str): given folder path
        add_slash_to_start (bool) : adds a slash to the start of the 

    Returns:
        str: path without the trailing slash
    """
    if len(path) == 0:
        return "/"
    lst = parse_directory_string(path)
    if not lst[0]:
        return "/"
    res = '/'.join(lst[1])
    if add_slash_to_start:
        res = "/" + res
    return res

def get_last_folder(path : str) -> str:
    """Returns the last folder in the given path

    Args:
        path (str): the path

    Returns:
        str: the last folder
    """
    if len(path) == 0:
        return "/"
    lst = parse_directory_string(path)
    if not lst[0]:
        return "/"
    return lst[1][-1]
