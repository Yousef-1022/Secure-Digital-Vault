from PyQt6.QtCore import QDir
from custom_exceptions.classes_exceptions import FileError

from crypto.utils import xor_magic
from utils.helpers import get_file_size, is_location_ok
from utils.constants import MAGIC_HEADER_START, MAGIC_HEADER_END, MAGIC_HEADER_PAD, CHUNK_LIMIT

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
        fd: FileDescriptor. It is given to reduce file opening overhead, and this function does not close it.

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
            # Reading
            if read_reverse:
                position = max(file.tell() - chunk_size, 0)
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
                if (file.tell() - chunk_size) == 0:
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
        print(f"Closing: {type(fd)} after override")
        fd.close()

def remove_bytes_from_ending_of_file(file_path : str, num_bytes : int) -> int:
    """Removes the specified amount of bytes from the file incase of failure.
    Location must be checked previously.

    Args:
        file_path (str): Location of the file.
        num_bytes (int): Number of bytes to remove

    Raises:

    Returns:
        int: Amount of remaining bytes in the file
    """
    size = get_file_size(file_path)
    if size < num_bytes:    # Cannot remove more bytes than what already exists
        return -1
    with open(file_path, "rb+") as file:
        file.seek(-num_bytes, 2)
        ans = file.truncate()
    return ans

def append_bytes_into_file(file_path : str , the_bytes : bytes, create_file : bool = False, file_name : str = "") -> tuple[bool,str,int,int]:
    """Adds the bytes into the given file. Can be used to insert for the vault itself.

    Args:
        file_path (str): File location on the disk
        the_bytes (bytes): Bytes which are already encrypted and serialized
        create_file (bool): Optional bool which is by default False, it creates the file if necessary.
        file_name (str) : Option str which is the file name. Used with create_file

    Returns:
        tuple[bool,str]: First value represents True upon success, False otherwise.
        Second value is if any error raised.
        Third value is the file_size before append.
        Fourth value is the file_size after append.
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
        return (False, e, init_size, new_size)
    except Exception as e:
        return (False, e, init_size, new_size)

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
        res = int(num)
    except ValueError:
        res = 0
    prev_error = append_error
    prev_error += f", Size is: '{res}'"
    added_bytes += already_add_bytes
    after_removal = remove_bytes_from_ending_of_file(file_path, added_bytes) # To remove anything added to the vault
    return f'{prev_error}, removal of appended {added_bytes} bytes makes new vault size: {after_removal} while the old size was: {old_size}'

def override_bytes_in_file(file_path : str , given_bytes : bytes, byte_loss : int,
                           at_location : int = 0, chunk_size : int = CHUNK_LIMIT, once : bool = True, fd  = None):
    """Adds the given bytes at a certain location of the file. Shifting is involved. Can be used to insert to the beginning of the file.

    Args:
        file_path (str): Location of the file
        given_bytes (bytes): The bytes to add

        byte_loss (int): The amount of bytes expected to be lost after adding into a certain index, e.g, 'test123' at_location 2
        with the addition of 'okay', assuming 'st' is to be replaced, then it would result in the loss of '12' (teokay3) which
        has the length of 2 and the final result must be 'teokay123'. Therefore, at the firstcall, simply calculate the amount
        of bytes to stuff - the length of what will it override. Use byte_loss = 0 if you want to overrwrite from specific place.
        Use byte_loss=len(byte_loss) to add into at_location without any loss and effectively shift the all bytes to the right.

        at_location (int, optional): Index location to start addition from. Defaults to 0.
        chunk_size (int): Chunk size to have in memory
        once (bool, optional): Boolean to mark the first iteration. MUST NOT BE USED AS IT IS USED BY RECURSION.
        fd: FileDescriptor. It is given to reduce file opening overhead. MUST NOT BE USED AS IT IS USED BY RECURSION.

        Returns:
            FileDescriptor (fd): FileDescriptor, which is to be closed by the caller.
    """
    print(f"overriding {file_path} at_location {at_location}, with byte_loss of: {byte_loss} and given_bytes of: {len(given_bytes)}")
    if len(given_bytes) == 0:
        print("given_bytes zero quit")
        return fd

    tmp = get_file_size(file_path)
    if tmp <= 0:
        if fd:
            fd.close()
        return None

    original_size = tmp
    save_location = at_location

    if fd:
        file = fd
    else:
        file = open(file_path , "rb+")

    file.seek(at_location+(len(given_bytes) - byte_loss))
    lost_chunk = file.read(chunk_size)
    file.seek(at_location)
    file.write(given_bytes)
    if once:
        file.write(lost_chunk[:byte_loss])
    save_location = file.tell()

    if save_location >= original_size:
        print("save_location quit")
        return fd
    if once:
        tmp_fd = override_bytes_in_file(file_path=file_path, given_bytes=lost_chunk[byte_loss:], byte_loss=byte_loss,
                               at_location=save_location, chunk_size=chunk_size, once=False, fd=file)
    else:
        tmp_fd = override_bytes_in_file(file_path=file_path, given_bytes=lost_chunk, byte_loss=byte_loss,
                               at_location=save_location, chunk_size=chunk_size, once=False, fd=file)
    return tmp_fd

def create_folder_on_disk(path : str) -> bool:
    """Creates a folder in the given path on the disk

    Args:
        path (str): The location, e.g, D:\\SomePath\\Location\\

    Returns:
        bool: True upon success, False otherwise
    """
    dir = QDir(path)
    return dir.mkpath(path)
