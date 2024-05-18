from custom_exceptions.utils_exceptions import MagicFailure
from custom_exceptions.classes_exceptions import DecryptionFailure

from utils.extractors import get_file_from_vault
from utils.constants import MAGIC_HEADER_START

from file_handle.file_io import find_header_pointers, find_footer_pointers

from crypto.utils import generate_aes_key
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def decrypt_bytes(ciphertext : bytes, password : str, key : bytes = None, iv : bytes = None) -> bytes:
    """
    Decrypts AES-encrypted bytes.

    Args:
        ciphertext (bytes): The ciphertext to decrypt.
        password (str): The password used for decryption.
        key (str, optional): Key generated by generate_aes_key , useful for large file decryption
        iv (bytes, optional): The initialization vector for AES

    Raises:
        DecryptionFailure incase it could not manage to decrypt the given bytes.

    Returns:
        bytes: The decrypted data.
    """
    pt_bytes = None
    try:
        # Large File Scenario
        if key and iv:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt_bytes = unpad(cipher.decrypt(ciphertext), AES.block_size)
        # Small File Scenario
        else:
            salt = ciphertext[:16]
            iv = ciphertext[16:32]
            ciphertext = ciphertext[32:]
            key = generate_aes_key(password=password.encode(), salt=salt, key_length=32)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt_bytes = unpad(cipher.decrypt(ciphertext), AES.block_size)
    except Exception as e:
        raise DecryptionFailure(f"Decryption failed due to: {e}")
    return pt_bytes

def decrypt_header(vault_location : str,  password : str) -> bytes:
    """Attempts to decrypt the header with the given password

    Args:
        vault_location (str): Location of the vault
        password (str): The password

    Raises:
        MagicFailure, DecryptionFailure

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
    res = decrypt_bytes(header, password)
    return res

def decrypt_footer(vault_location : str,  password : str) -> list:
    """Attempts to decrypt the footer with the given password

    Args:
        vault_location (str): Location of the vault
        password (str): The password

    Raises:
        MagicFailure, DecryptionFailure

    Returns:
        list: [0] index is int of the footer Start, [1] index is the decrypted footer as dict bytes
    """
    res = find_footer_pointers(vault_location)
    if res[0] == -1 or res[1] == -1:
        return [-1, b'']
    footer_start = res[0]
    footer_end   = res[1]
    footer = get_file_from_vault(vault_location, footer_start, footer_end)
    res = decrypt_bytes(footer, password)
    return [footer_start, res]
