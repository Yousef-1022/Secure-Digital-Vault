from PyQt6.QtCore import QDir, QFile
from custom_exceptions.classes_exceptions import FileError

from utils.extractors import get_file_from_vault
from crypto.utils import xor_magic
from utils.helpers import get_file_size, is_location_ok
from utils.constants import MAGIC_HEADER_START, MAGIC_HEADER_END, MAGIC_HEADER_PAD, CHUNK_LIMIT, MAGIC_LOG_START, MAGIC_LOG_END

import os


def find_magic(vault_path: str, magic_bytes: bytes, start_from_index: int = -1, read_reverse: bool = False,
               chunk_size: int = CHUNK_LIMIT, fd = None) -> int:
    """Finds the magic bytes in the given vault_path. It is required to remove the length of the end magic bytes after caluclating
    both Begin,End , as the index returned is after the magic bytes, e.g., <magic>_

    Args:
        vault_path (str): vault location on disk
        magic_bytes (bytes): Magic bytes to search (Must be deserialized)
        start_from_index (int): optional Index where to start search from
        read_reverse (bool): optional value to read the file from the ending
        chunk_size (int, optional): Chunk size to read which has length bigger than Magic.
        fd: FileDescriptor. It is given to reduce file opening overhead, and this function does not close it. (rb)

    Returns:
        int: Ending Index of the magic bytes. -1 if it does not exist.
        If fd is not None, then the caller must close it.
    """

    result = -1

    if chunk_size < len(magic_bytes):
        return result

    if not fd:
        file = open(vault_path, "rb")
    else:
        file = fd

    try:
        # Get File Size
        file.seek(0, 2)
        file_size = file.tell()

        if start_from_index != -1:
            file.seek(start_from_index)
        elif read_reverse:
            file.seek(0, 2)
        else:
            file.seek(0, 0)

        while True:
            chunk = None
            position = 0
            end_reverse = False
            # Reading
            if read_reverse:
                position = max(file.tell() - chunk_size, 0)
                if position == 0:
                    end_reverse = True
                file.seek(position)
            chunk = file.read(chunk_size)
            if not chunk:
                result = -1
                break
            # Index find
            index = chunk.find(magic_bytes)
            if index != -1:
                actual_index = file.tell() - len(chunk) + index + len(magic_bytes)
                result = actual_index
                break
            # Edge case of magic being separated between two chunks.
            if read_reverse:
                if end_reverse:
                    break
                if (file.tell() - chunk_size) <= 0:
                    result = -1
                    break
                file.seek(min(position+len(magic_bytes),file_size))
            else:
                if file.tell() == file_size:
                    result = -1
                    break
                file.seek(max(file.tell()-len(magic_bytes),0))
    except Exception:
        result = -1
    finally:
        if not fd:
            file.close()
    return result

def find_header_pointers(vault_path : str) -> list[int]:
    """Returns a list related to the indexes of the header. The vault path must be checked before.

    Args:
        vault_path (str): Location of the vault

    Returns:
        list[int]: [0] index is the length of the pad for the header.
        [1] index is the length of the encrypted header on the disk.
        [2], [3], and [4] indexes are the 'starting' loc of: MAGIC_HEADER_START, MAGIC_HEADER_PAD, MAGIC_HEADER_END
    """
    magic_start = xor_magic(MAGIC_HEADER_START)
    magic_pad   = xor_magic(MAGIC_HEADER_PAD)
    magic_end   = xor_magic(MAGIC_HEADER_END)

    file = open(vault_path, "rb")
    header_start = find_magic(vault_path, magic_start, fd=file)
    header_pad   = find_magic(vault_path, magic_pad, start_from_index=header_start, fd=file)
    header_end   = find_magic(vault_path, magic_end, start_from_index=header_pad, fd=file)
    file.close()

    pad_length    = (header_end - len(magic_end)) - header_pad
    header_length = (header_pad - len(magic_pad)) - header_start
    return [pad_length, header_length, header_start-len(magic_start), header_pad-len(magic_pad), header_end-len(magic_end)]

def add_magic_into_header(bytes_as_dict: bytes, start_only: bool = True, pad_only: bool = True, end_only: bool = True) -> bytes:
    """Adds the relevant magic bytes into the serialized and encrypted dict

    Args:
        bytes_as_dict (bytes): Serialized and Encrypted dict
        start_only (bool): If to add HEADER_START only
        pad_only (bool): If to add HEADER_PAD only
        end_only (bool): If to add HEADER_END only

    Returns:
        bytes: Same bytes but with the magic bytes at the beginning, after the dict, and at the end of the dict.
    """
    return_dict = b''
    if start_only:
        return_dict += xor_magic(MAGIC_HEADER_START)
    return_dict += bytes_as_dict
    if pad_only:
        return_dict += xor_magic(MAGIC_HEADER_PAD)
    if end_only:
        return_dict += xor_magic(MAGIC_HEADER_END)
    return bytes(return_dict)

def header_padder(file_path : str , amount_to_pad : int) -> None:
    """Pads the header on the disk with the given amount of padding. This amount is taken from the serialized decrypted header size.

    Args:
        file_path (str): Location of the vault
        amount_to_pad (int): amount of bytes to fill
    """
    res = is_location_ok(file_path, for_file_save=False, for_file_update=True)
    if not res[0]:
       raise FileError(res[1])
    xored_pad = xor_magic(MAGIC_HEADER_PAD)
    hdr_pad_loc = find_magic(file_path, xored_pad)
    pad_bytes = os.urandom(amount_to_pad)
    fd = override_bytes_in_file(file_path=file_path, given_bytes=pad_bytes, byte_loss=len(pad_bytes), at_location=hdr_pad_loc)
    if fd:
        fd.close()

def find_footer_pointers(vault_path : str) -> tuple[int,int]:
    """Returns a list related to the indexes of the footer. The vault path must be checked before.

    Args:
        vault_path (str): Location of the vault

    Returns:
        tuple[int]: [0] index is the start of the footer after the magic bytes, [1] index is the end of the footer before the magic bytes
    """
    magic_start = xor_magic(MAGIC_LOG_START)
    magic_end   = xor_magic(MAGIC_LOG_END)
    file = open(vault_path, "rb")

    footer_start = find_magic(vault_path, magic_start, read_reverse=True, fd=file)
    footer_end   = find_magic(vault_path, magic_end, read_reverse=True, fd=file)
    file.close()
    return footer_start, footer_end-len(magic_end)

def add_magic_into_footer(bytes_as_dict: bytes) -> bytes:
    """Adds the relevant magic bytes into the serialized and encrypted dict

    Args:
        bytes_as_dict (bytes): Serialized and Encrypted dict

    Returns:
        bytes: Same bytes but with the magic bytes at the beginning, and at the end of the dict.
    """
    return_dict = xor_magic(MAGIC_LOG_START)
    return_dict += bytes_as_dict
    return_dict += xor_magic(MAGIC_LOG_END)
    return bytes(return_dict)

def remove_bytes_from_ending_of_file(file_path : str, num_bytes : int, fd = None) -> int:
    """Removes the specified amount of bytes from the file incase of failure.
    Location must be checked previously.

    Args:
        file_path (str): Location of the file.
        num_bytes (int): Number of bytes to remov
        FileDescriptor (fd) optional: FileDescriptor, which is to be closed by the caller if provided (rb+).

    Returns:
        int: Amount of remaining bytes in the file
    """
    size = get_file_size(file_path)
    if size < num_bytes:    # Cannot remove more bytes than what already exists
        return -1

    if fd:
        file = fd
    else:
        file = open(file_path, "rb+")

    file.seek(-num_bytes, 2)
    ans = file.truncate()
    if not fd:
        file.close()
    return ans

def append_bytes_into_file(file_path : str , the_bytes : bytes, create_file : bool = False, file_name : str = "") -> tuple[bool,str,int,int]:
    """Adds the bytes into the given file. Can be used to insert for the vault itself.

    Args:
        file_path (str): File location on the disk
        the_bytes (bytes): Bytes which are already encrypted and serialized
        create_file (bool): Optional bool which is by default False, it creates the file if necessary.
        file_name (str) : Option str which is the file name. Used with create_file

    Returns:
        tuple[bool,str,int,int]: [0] represents True upon success, False otherwise.
        [1] is if any error raised.
        [2] is the file_size before append.
        [3] is the file_size after append.
    """
    if create_file:
        result = is_location_ok(file_path, for_file_save=create_file, for_file_update=False)
    else:
        result = is_location_ok(file_path, for_file_save=create_file, for_file_update=True)
    if not result[0]:
        return (False, f'{result[1]}, appended: 0', 0,0)
    init_size = 0
    new_size = 0
    try:
        amount_of_bytes = len(the_bytes)
        written_bytes = 0
        if create_file:
            with open(f'{file_path}/{file_name}' , "wb") as f:
                written_bytes = f.write(the_bytes)
        else:
            res = get_file_size(file_path)
            if res <= 0 :
                raise FileError(f"File: {file_path} has size of '{res}', appended: 0")
            init_size = res
            with open(file_path , "ab") as f:
                written_bytes = f.write(the_bytes)

            res = get_file_size(file_path)
            new_size = res
            if res - init_size != len(the_bytes):
                raise FileError(f"Appending Failure. Old size: {init_size} != New size: {res} after append. Total bytes to add: {amount_of_bytes}, appended: {written_bytes}")
        if written_bytes != amount_of_bytes:
            raise FileError(f"Appending Failure. Old size: {init_size} != New size: {res} after append. Total bytes to add: {amount_of_bytes}, appended: {written_bytes}")
        return (True, "", init_size, new_size)
    except FileError as e:
        return (False, e.message, init_size, new_size)
    except Exception as e:
        return (False, e.__str__(), init_size, new_size)

def stabilize_after_failed_append(file_path : str, append_error : str, old_size : int, already_add_bytes : int = 0):
    """Handle scenario incase append_bytes_into_file function returns False.

    Args:
        file_path (str): The location of the file, must be correct by default.
        append_error (str): Error given by the append_bytes_into_file function.
        old_size (int): Init size of the file.
        already_add_bytes (int, optional): Already added bytes. Defaults to 0.

    Returns:
        str: Process string error of what happened.
    """
    word = "appended:"
    location = append_error.rfind(word)
    num = append_error[location+len(word):].strip()
    added_bytes = 0
    try:
        added_bytes = int(num)
    except ValueError:
        added_bytes = 0
    prev_error = append_error
    prev_error += f", Size is: '{added_bytes}'"
    added_bytes += already_add_bytes
    after_removal = remove_bytes_from_ending_of_file(file_path, added_bytes) # To remove anything added to the vault
    return f'{prev_error}, removal of appended {added_bytes} bytes makes new vault size: {after_removal} while the old size was: {old_size}'

def override_bytes_in_file(file_path : str , given_bytes : bytes, byte_loss : int,
                           at_location : int = 0, chunk_size : int = CHUNK_LIMIT, fd  = None):
    """Adds the given bytes at a certain location of the file. Shifting is involved. Can be used to insert to the beginning of the file.

    Args:
        file_path (str): Location of the file
        given_bytes (bytes): The bytes to add

        byte_loss (int): The amount of bytes expected to be lost after adding into a certain index.
        - Use byte_loss = 0 if you want to overrwrite from specific place and not push any bytes after at_location argument,
            e.g, 'test123' at_location 3 with the addition of 'hey', will get the result (teshey3)
        - Use byte_loss=len(byte_loss) to add into at_location without any loss and effectively shift the all bytes to the right,
            e.g, 'test123' at_location 4 with the addition of 'okay', will get the result (testokay123)

        at_location (int, optional): Index location to start addition from. Defaults to 0.
        chunk_size (int): Chunk size to have in memory, if given bytes amount is larger than the CHUNK_LIMIT must be >= given_bytes
        fd: FileDescriptor. It is given to reduce file opening overhead. (rb+)

        Returns:
            FileDescriptor (fd): FileDescriptor, which is to be closed by the caller. (rb+)
    """
    if len(given_bytes) == 0:
        return fd

    tmp = get_file_size(file_path)
    if tmp <= 0:
        if fd:
            fd.close()
        return None

    if fd:
        file = fd
    else:
        file = open(file_path , "rb+")

    # Next move
    move = len(given_bytes) - byte_loss
    if move < 0:
        move = 0
    elif tmp < (at_location + move):
        move = 0

    # Grab Lost Chunk
    file.seek(at_location+move)
    lost_chunk = file.read(chunk_size)
    file.seek(at_location)

    # Write the given bytes
    file.write(given_bytes)
    save_location = file.tell()

    # Determine next byte loss
    written = len(given_bytes)
    file.seek(0,2)
    remaining = file.tell() - save_location
    file.seek(save_location)
    next_byte_loss = len(lost_chunk)-written

    # If next byte loss is negative, then it went over the file
    if next_byte_loss < 0:
        if file.tell() < tmp:
            file.write(lost_chunk)
        elif remaining == 0:
            file.seek(0,2)
            file.seek(file.tell()-byte_loss)
            file.write(lost_chunk)
        return file

    if (len(lost_chunk) == 0):
        return file

    file = override_bytes_in_file(file_path=file_path, given_bytes=lost_chunk, byte_loss=next_byte_loss,
                           at_location=save_location, chunk_size=chunk_size, fd=file)
    return file

def delete_bytes_from_file(file_path : str, bytes_to_delete : int, start_index : int, chunk_size : int = CHUNK_LIMIT, fd = None) -> int:
    """Deletes bytes from the given spot in the file using recursion and inplace overwrite.

    Args:
        file_path (str): The location of the file
        bytes_to_delete (int): Amount of bytes to delete
        start_index (int): The location of the index to start the deletion from
        chunk_size (int, optional): The Size of the chunk to read during every iteration. Defaults to CHUNK_LIMIT.
        fd: FileDescriptor. It is given to reduce file opening overhead. Must be closed if given by the caller (rb+)

    Returns:
        int: The remaining amount of bytes in the file after delete
    """
    if fd:
        file = fd
    else:
        file = open(file_path, "rb+")

    init_chunk_start = start_index + bytes_to_delete
    init_chunk_end = init_chunk_start + bytes_to_delete
    next_chunk = get_file_from_vault(vault_path=file_path, starting_byte=init_chunk_start, ending_byte=init_chunk_end,
                                     chunk_size_to_read=chunk_size, fd=file)
    if len(next_chunk) < bytes_to_delete:
        file = override_bytes_in_file(file_path=file_path, given_bytes=next_chunk, byte_loss=0,
                                      at_location=start_index, chunk_size=chunk_size, fd=file)
        res = remove_bytes_from_ending_of_file(file_path, bytes_to_delete, fd=file)
        return res

    # Override what is to delete
    file = override_bytes_in_file(file_path=file_path, given_bytes=next_chunk, byte_loss=0,
                                  at_location=start_index, chunk_size=chunk_size, fd=file)
    # Push
    override_from = init_chunk_start
    next_chunk_start = init_chunk_end # Skip initial replacement chunk
    next_chunk_end = next_chunk_start + chunk_size
    while True:
        chunk = get_file_from_vault(vault_path=file_path, starting_byte=next_chunk_start, ending_byte=next_chunk_end,
                                    chunk_size_to_read=chunk_size, fd=file)
        if not chunk:
            break
        file = override_bytes_in_file(file_path=file_path, given_bytes=chunk, byte_loss=0,
                                      at_location=override_from, chunk_size=chunk_size, fd=file)
        override_from = override_from + len(chunk)
        next_chunk_start = next_chunk_end
        next_chunk_end = next_chunk_end + chunk_size

    res = remove_bytes_from_ending_of_file(file_path, bytes_to_delete, fd=file)
    if not fd:
        file.close()
    return res

def delete_footer_and_hint(file_path : str, footer_start_index : int):
    """Deletes the footer including the MAGIC and the hint associated with the vault

    Args:
        file_path (str): The location of the vault
        footer_start_index (int): The starting index of the footer
    """
    the_size = get_file_size(file_path)
    to_remove = the_size - (footer_start_index - len(MAGIC_LOG_START))
    remove_bytes_from_ending_of_file(file_path, to_remove)

def add_footer_and_hint(file_path : str, footer_bytes : bytes, the_hint : str):
    """Adds the encrypted footer into the vault path

    Args:
        file_path (str): The location of the vault
        footer_bytes (bytes): The encrypted footer
        the_hint (str): The hint
    """
    footer = add_magic_into_footer(footer_bytes)
    footer += xor_magic(the_hint)
    append_bytes_into_file(file_path, footer, create_file=False)

def get_hint(file_path : str) -> str:
    """Gets the hint associated with Vault

    Args:
        file_path (str): Location of the vault

    Returns:
        str: The Hint itself
    """
    footer_end = xor_magic(MAGIC_LOG_END)
    fd = open(file_path, "rb")
    loc = find_magic(file_path, footer_end, read_reverse=True, chunk_size=int(CHUNK_LIMIT/10), fd=fd)
    if loc == -1:
        fd.close()
        return "No Hint Detected"
    fd.seek(loc)
    hint = fd.read(32)
    fd.close()
    return xor_magic(hint.decode()).decode()

def create_folder_on_disk(path : str) -> bool:
    """Creates a folder in the given path on the disk

    Args:
        path (str): The location, e.g, D:\\SomePath\\Location\\

    Returns:
        bool: True upon success, False otherwise
    """
    dir = QDir(path)
    return dir.mkpath(path)

def rename_file(file_path : str, new_name : str) -> tuple[bool,str]:
    """Checks whether its possible to rename the file and the renames it

    Args:
        file_path (str): The location of the file to check if it can be renamed. This location must be valid in Windows Style.
        new_name (str): The new name.

    Returns:
        tuple[bool,str]: [0] True if possible, False otherwise. [1] reason for False or full new path if True
    """
    if not QFile.exists(file_path):
        return False, f"'{file_path}' does not exist!"
    idx = file_path.rfind("\\")
    old_name = file_path[idx+1:]
    if old_name == new_name:
        return False, f"Old name cannot be the same as the new name!"
    location = file_path[:idx+1] + new_name
    if QFile.exists(location):
        return False, f"Cannot rename to '{location}' because it exists!"
    f = QFile(file_path)
    res = f.rename(new_name)
    if not res:
        return res, f"Failure to rename to '{new_name}'"
    else:
        return res, location
