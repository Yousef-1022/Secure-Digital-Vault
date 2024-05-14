from custom_exceptions.utils_exceptions import MagicFailure
from custom_exceptions.classes_exceptions import DecryptionFailure

from utils.extractors import get_file_from_vault
from utils.constants import MAGIC_HEADER_START

from file_handle.file_io import find_header_pointers


# To decrypt, how about you find the requested header, and see if you were able to decrypt it. S
def decrypt_header(vault_location : str,  password : str) -> bytes:
    """Attempts to decrypt the header with the given password

    Args:
        vault_location (str): Location of the vault
        password (str): The password

    Returns:
        dict: The decrypted header as dict
    """
    error = ""
    magic_start_len = len(MAGIC_HEADER_START)
    res = find_header_pointers(vault_location)
    if len(res) < 5:
        raise MagicFailure(f"Couldn't find the header pointers. List result is {res}")
    header_start = res[2]
    header_pad   = res[3]
    header_end   = res[4]
    if header_start < 0:
        error += "Couldn't find the beginning of the header. "
    if header_end < 0:
        error += "Couldn't find the end of the header."
    if header_pad < 0:
        error += "Couldn't find the pad magic of the header."
    if len(error) != 0:
        raise MagicFailure(error)
    header = get_file_from_vault(vault_location, header_start+magic_start_len, header_pad)
    #TODO: DECRYPT HEADER
    return header

def decrypt_password_storage(password : bytes) -> str:
    """Decrypts the vault password for tmp storage

    Args:
        password (str): Password of the vault

    Returns:
        str: Decrypted password
    """
    #TODO: Decrypt password tmp storage
    return str(password)