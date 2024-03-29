
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
