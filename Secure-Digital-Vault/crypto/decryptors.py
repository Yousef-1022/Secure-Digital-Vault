from custom_exceptions.utils_exceptions import MagicFailure
from custom_exceptions.classes_exceptions import DecryptionFailure

from utils.extractors import find_magic , get_file_from_vault
from utils.constants import MAGIC_HEADER_START, MAGIC_HEADER_END
from utils.parsers import parse_json_safely

from crypto.utils import xor_magic

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
    header_start = find_magic(vault_location, magic_start,read_reverse=True)
    header_end =   find_magic(vault_location, magic_end)
    if header_start == -1:
        error += "Couldn't find the beginning of the header. "
    if header_end == -1:
        error += "Couldn't find the end of the header."
    if len(error) != 0:
        raise MagicFailure(error)
    header = get_file_from_vault(vault_location, header_start, header_end-len(magic_end))
    ### TODO: DECRYPT HEADER
    return header
