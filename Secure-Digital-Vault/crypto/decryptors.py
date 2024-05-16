from custom_exceptions.utils_exceptions import MagicFailure
from custom_exceptions.classes_exceptions import DecryptionFailure

from utils.extractors import get_file_from_vault
from utils.constants import MAGIC_HEADER_START

from file_handle.file_io import find_header_pointers

from crypto.utils import generate_aes_key
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def decrypt_bytes(ciphertext : bytes, password : str) -> bytes:
    """
    Decrypts AES-encrypted bytes.

    Args:
        ciphertext (bytes): The ciphertext to decrypt.
        password (str): The password used for decryption.

    Raises:
        DecryptionFailure incase it could not manage to decrypt the given bytes.

    Returns:
        bytes: The decrypted data.
    """
    pt_bytes = None
    try:
        salt = ciphertext[:16]
        iv = ciphertext[16:32]
        ciphertext = ciphertext[32:]
        key = generate_aes_key(password.encode(), salt, 32)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt_bytes = unpad(cipher.decrypt(ciphertext), AES.block_size)
    except Exception as e:
        raise DecryptionFailure(f"Invalid password raised exception: {e}")
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
