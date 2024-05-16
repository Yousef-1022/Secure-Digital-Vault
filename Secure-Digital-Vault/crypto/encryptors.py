from custom_exceptions.classes_exceptions import FileError, EncryptionFailure
from file_handle.file_io import append_bytes_into_file, stabilize_after_failed_append
from utils.extractors import get_icon_from_file

from utils.helpers import get_file_size
from utils.constants import CHUNK_LIMIT
from crypto.utils import generate_aes_key

from gui.threads.mutable_boolean import MutableBoolean

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad


def encrypt_bytes(data : bytes, password : str) -> bytes:
    """
    Encrypts bytes using AES encryption in CBC mode.

    Args:
        data (bytes): The data to encrypt.
        password (str): The password used for encryption.

    Returns:
        bytes: The encrypted data.
    """
    res = None
    try:
        iv = get_random_bytes(16)
        salt = get_random_bytes(16)
        key = generate_aes_key(password.encode(), salt, 32)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        res = salt + iv + ct_bytes
    except Exception as e:
        raise EncryptionFailure(e)
    return res

def encrypt_header(password : str , header : bytes) -> bytes:
    """Encrypts the header with AES

    Args:
        password (str): Password.
        header (bytes): Serialized header.

    Info:
        Potential failure in Encryption could be raised, but as the header is always a valid json, this is not ought to happen.

    Returns:
        bytes: Encrypted header.
    """
    result = encrypt_bytes(header, password)
    return result

def get_file_and_encrypt_and_add_to_vault(password : str, file_path : str, vault_path : str, continue_running : MutableBoolean,
                                          chunk_size : int = CHUNK_LIMIT) -> list:
    """Gets the file as bytes, encrypts during reading to avoid memory overhead, and adds it to the vault on disk. Also, adds the icon.

    Args:
        password (str): Password of the vault.
        file_path (str): File location.
        vault_path (str): Vault path
        keep_running (MutableBoolean): Boolean to abort process
        chunk_size (int): Chunk size to read.

    Raises:
        FileError, EncryptionFailure incase it was not able to handle failure

    Returns:
        list: [0] index is: file_loc_start, [1] index is: file_loc_end, [2] index is: encrypted_file_size,
        [3] is: icon_loc_start, [4] is: icon_loc_end.
        If less values than 5 are returned, then an error has occured.
        4 values indicate that the addition of the file itself was fine, but last value is the error.
    """
    if not continue_running.get_value():
        return []
    ans = []
    res = get_file_size(vault_path)
    if res <= 0:
        raise FileError(f"File: {vault_path} at initial stage has size of '{res}'!")
    vault_size = res

    loc_start = vault_size
    ans.append(loc_start)

    file_size = res
    encrypted_file_size = 0
    added_bytes = 0

    with open(file_path, "rb") as file:
        while continue_running.get_value():
            chunk = None
            chunk = file.read(chunk_size)
            if not chunk:
                break

            # Encrypt
            try:
                chunk = encrypt_bytes(chunk, password)
            except EncryptionFailure as e:
                continue_running.set_value(False)
                error_str = stabilize_after_failed_append(vault_path, e.message, vault_size, added_bytes)
                raise EncryptionFailure(f"Removed added bytes, but failure happened during encryption: {error_str}")

            encrypted_file_size += len(chunk)
            if not continue_running.get_value():
                break

            # Append
            res = append_bytes_into_file(file_path=vault_path, the_bytes=chunk)

            if not res[0] or not continue_running.get_value():
                continue_running.set_value(False)
                error_str = stabilize_after_failed_append(vault_path, res[1], res[2], added_bytes)
                raise FileError(f"Removed added bytes, but failure happened after appending bytes: {error_str}")

            added_bytes += len(chunk)
            if file.tell() == file_size:
                break

    res = get_file_size(vault_path)
    new_vault_size = res

    loc_end = new_vault_size
    ans.append(loc_end)
    ans.append(encrypted_file_size)
    # From this point onward its fine to add file into vault because the answer list has 3 values at least

    if not continue_running.get_value():
        ans.append("Continue running is turned off!")
        return ans

    file_icon = get_icon_from_file(file_path)

    icon_start = loc_end
    res = append_bytes_into_file(file_path=vault_path, the_bytes=file_icon)
    if not res[0]:
        prev_error = stabilize_after_failed_append(vault_path, res[1], res[2], res[3]-res[2])
        prev_error += ", the file has no icon bytes"
        ans.append(prev_error)
        return ans

    # Icon tuple + EncryptedFileSize
    res = get_file_size(vault_path)
    icon_end = res

    ans.append(icon_start)
    ans.append(icon_end)
    return ans
