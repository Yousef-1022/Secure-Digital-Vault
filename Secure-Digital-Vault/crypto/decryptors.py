from custom_exceptions.utils_exceptions import MagicFailure
from custom_exceptions.classes_exceptions import DecryptionFailure

from utils.extractors import get_file_from_vault
from utils.constants import MAGIC_HEADER_START, MAGIC_HEADER_PAD ,MAGIC_HEADER_END

from crypto.utils import xor_magic
from file_handle.file_io import find_magic


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
    magic_start = xor_magic(MAGIC_HEADER_START)
    magic_end = xor_magic(MAGIC_HEADER_END)
    magic_pad = xor_magic(MAGIC_HEADER_PAD)
    header_start = find_magic(vault_location, magic_start)
    header_end =   find_magic(vault_location, magic_end)
    header_pad =   find_magic(vault_location, magic_pad)
    if header_start == -1:
        error += "Couldn't find the beginning of the header. "
    if header_end == -1:
        error += "Couldn't find the end of the header."
    if header_pad == -1:
        error += "Couldn't find the pad magic of the header."
    if len(error) != 0:
        raise MagicFailure(error)
    header = get_file_from_vault(vault_location, header_start, header_pad-len(magic_pad))
    ### TODO: DECRYPT HEADER
    return header

def decrypt_password_storage(password : bytes) -> str:
    """Decrypts the vault password for tmp storage

    Args:
        password (str): Password of the vault

    Returns:
        str: Decrypted password
    """
    ### TODO: Decrypt password tmp storage
    return str(password)