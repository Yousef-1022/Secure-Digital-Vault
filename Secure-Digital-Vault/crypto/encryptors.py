from custom_exceptions.classes_exceptions import FileError
from file_handle.file_io import append_bytes_into_file, remove_bytes_from_file
from utils.extractors import get_icon_from_file
from utils.helpers import get_file_size

from gui.threads.mutable_boolean import MutableBoolean


def encrypt_header(password : str , header : bytes) -> bytes:
    """Encrypts the header with PLACEHOLDER

    Args:
        password (str): Password.
        header (bytes): Serialized header.

    Returns:
        bytes: Encrypted header.
    """
    # TODO: Encrypt header
    return header

def get_file_and_encrypt_and_add_to_vault(password : str, file_path : str, vault_path : str, continue_running : MutableBoolean , chunk_size : int = 4096) -> list[int]:
    """Gets the file as bytes, encrypts during reading to avoid memory overhead, and adds it to the vault. Also, adds the icon.

    Args:
        password (str): Password of the vault.
        file_path (str): File location.
        vault_path (str): Vault path
        keep_running (MutableBoolean): Boolean to abort process
        chunk_size (int): Chunk size to read.

    Returns:
        list[int]: First two values represent where the file starts and ends, second two values represent where the icon starts and ends. Last Value is Size.
    """
    if not continue_running.get_value():
        return []
    ans = []
    res = get_file_size(vault_path)
    if res[0] < 1:
        raise FileError(res[1])
    vault_size = res[0]
    print(f"vault_size ({vault_size}) before adding: ({file_path})")
    loc_start = vault_size
    ans.append(loc_start)

    file_size = res[0]
    encrypted_file_size = 0

    # TODO: Lock vault file with OS before appending. PASS ABORT BOOLEAN
    with open(file_path, "rb") as file:
        while continue_running.get_value():
            chunk = None
            chunk = file.read(chunk_size)
            if not chunk:
                break

            chunk = encrypt_bytes(password, chunk)
            encrypted_file_size += len(chunk)
            if not continue_running.get_value():
                break
            res = append_bytes_into_file(file_path=vault_path, the_bytes=chunk)

            if not res[0] or not continue_running.get_value():
                prev_error = res[1]
                res = get_file_size(vault_path)
                prev_error += res[1]
                try:
                    remove_bytes_from_file(vault_path, res[0] - vault_size) # To remove anything added to the vault
                except Exception as e:
                    prev_error += e
                raise FileError(prev_error)

            if file.tell() == file_size:
                break
    # TODO: Close lock

    res = get_file_size(vault_path)
    if res[0] < 1:
        raise FileError(res[1])
    new_vault_size = res[0]
    if new_vault_size - vault_size != encrypted_file_size:
        raise FileError(f"OldVaultSize: {vault_size}, NewSize: {new_vault_size}, EncryptedFileSize: {encrypted_file_size}. MISMATCH! . OldError: {res[1]}")
    print(f"vault_size ({new_vault_size}) after adding: ({file_path})")

    loc_end = new_vault_size
    ans.append(loc_end)
    prev_error = ""
    if not continue_running.get_value():
        return []

    file_icon = get_icon_from_file(file_path)

    icon_start = loc_end
    res = append_bytes_into_file(file_path=vault_path, the_bytes=file_icon)
    if not res[0]:
        raise FileError(res[1])
    # Icon tuple + EncryptedFileSize
    res = get_file_size(vault_path)
    if res[0] < 1:
        raise FileError(res[1])

    icon_end = res[0]
    print(f"vault_size ({icon_end}) after icon adding of: ({file_path})")
    ans.append(icon_start)
    ans.append(icon_end)
    ans.append(encrypted_file_size)
    print(f"THE LIST: {ans}")
    return ans

def encrypt_bytes(password : str , byte_chunk : bytes) -> bytes:
    """Encrypts the given file bytes

    Args:
        password (str): Password of the vault
        byte_chunk (bytes): A byte chunk from the file itself

    Returns:
        bytes: The encrypted file
    """
    # TODO: Encrypt byte_chunk
    return byte_chunk

def encrypt_password_storage(password : str) -> bytes:
    """Encrypts the vault password for tmp storage

    Args:
        password (str): Password of the vault

    Returns:
        bytes: Encrypted password
    """
    # TODO: Encrypt password tmp storage
    return password.encode()
