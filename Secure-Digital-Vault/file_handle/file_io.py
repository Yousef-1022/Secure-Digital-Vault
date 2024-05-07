from custom_exceptions.classes_exceptions import FileError

from crypto.utils import xor_magic
from utils.helpers import get_file_size, is_location_ok
from utils.constants import MAGIC_HEADER_START, MAGIC_HEADER_END, MAGIC_HEADER_PAD

import os


def find_magic(vault_path: str, magic_bytes: bytes, start_from_index: int = -1, read_reverse: bool = False, chunk_size: int = 4096) -> int:
    """Finds the magic bytes in the given vault_path. It is required to remove the length of the end magic bytes after caluclating
    both Begin,End , as the index returned is after the magic bytes, e.g., <magic>_

    Args:
        vault_path (str): vault location on disk
        magic_bytes (bytes): Magic bytes to search (Must be deserialized)
        start_from_index (int): optional Index where to start search from
        read_reverse (bool): optional value to read the file from the ending
        chunk_size (int, optional): Chunk size to read which has length bigger than Magic. Defaults to 4096.

    Returns:
        int: Ending Index of the magic bytes. -1 if it does not exist.
    """
    if chunk_size < len(magic_bytes):
        return -1
    with open(vault_path, "rb") as file:
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
                return -1
            # Index find
            index = chunk.find(magic_bytes)
            if index != -1:
                actual_index = file.tell() - len(chunk) + index + len(magic_bytes)
                return actual_index
            # Edge case of magic being separated between two chunks.
            if read_reverse:
                if (file.tell() - chunk_size) == 0:
                    return -1
                file.seek(min(position+len(magic_bytes),file_size))
            else:
                if file.tell() == file_size:
                    return -1
                file.seek(max(file.tell()-len(magic_bytes),0))

def find_pad_length_of_header(vault_path : str) -> int:
    """Returns the length of the pad in the header

    Args:
        vault_path (str): Location of the vault

    Returns:
        int: the length of the pad for the header.
    """
    magic_pad  = xor_magic(MAGIC_HEADER_PAD)
    magic_end  = xor_magic(MAGIC_HEADER_END)
    header_pad = find_magic(vault_path, magic_pad)
    header_end = find_magic(vault_path, magic_end) - len(magic_end) # find_magic returns index after magic
    if header_end == -1 or header_pad == -1:
        return -1
    return header_end-header_pad

def find_header_length(vault_path : str) -> int:
    """Returns the length of the encrypted header on the disk

    Args:
        vault_path (str): Location of the vault

    Returns:
        int: the length of the encrypted header
    """
    magic_start  = xor_magic(MAGIC_HEADER_START)
    magic_pad    = xor_magic(MAGIC_HEADER_PAD)
    header_start = find_magic(vault_path, magic_start)
    header_pad   = find_magic(vault_path, magic_pad) - len(magic_pad) # find_magic returns index after magic
    if header_start == -1 or header_pad == -1:
        return -1
    return header_pad-header_start

def append_bytes_into_file(file_path : str , the_bytes : bytes, create_file : bool = False, file_name : str = "") -> tuple[bool,str]:
    """Adds the bytes into the given file. Can be used to insert for the vault itself.

    Args:
        file_path (str): File location on the disk
        the_bytes (bytes): Bytes which are already encrypted and serialized
        create_file (bool): Optional bool which is by default False, it creates the file if necessary.
        file_name (str) : Option str which is the file name. Used with create_file

    Returns:
        tuple[bool,str]: First value represents True upon success, False otherwise. Second value is if any error raised.
    """
    if create_file:
        result = is_location_ok(file_path, for_file_save=create_file, for_file_update=False)
    else:
        result = is_location_ok(file_path, for_file_save=create_file, for_file_update=True)
    if not result[0]:
        return False , result[1]
    try:
        amount_of_bytes = len(the_bytes)
        written_bytes = 0
        if create_file:
            with open(f'{file_path}/{file_name}' , "ab") as f:
                written_bytes = f.write(the_bytes)
        else:
            res = get_file_size(file_path)
            if res[0] < 0 :
                raise FileError(res[1])
            init_size = res[0]
            with open(file_path , "ab") as f:
                written_bytes = f.write(the_bytes)

            res = get_file_size(file_path)
            if res[0] - init_size != len(the_bytes):
                raise FileError(f"Old size: {init_size} != New size: {res[0]} - Bytes to append: {amount_of_bytes}, appended: {written_bytes}. {res[1]}")
        if written_bytes != amount_of_bytes:
            raise FileError(f"Appended Failure. Old size: {init_size} != New size: {res[0]} - Bytes to append: {amount_of_bytes}, appended: {written_bytes}. {res[1]}")
        return True, ""
    except FileError as e:
        return False,e
    except Exception as e:
        return False,e

def remove_bytes_from_file(file_path : str, num_bytes : int) -> bool:
    """Removes the specified amount of bytes from the file incase of failure.

    Args:
        file_path (str): Location of the file.
        num_bytes (int): Number of bytes to remove

    Returns:
        bool: Boolean value upon success
    """
    res = is_location_ok(location_path=file_path, for_file_save=False,for_file_update=True)
    if not res[0]:
        raise FileError(res[1])
    with open(file_path, "rb+") as file:
        file.seek(-num_bytes, 2)
        file.truncate()
    return True

def override_bytes_in_file(file_path : str , given_bytes : bytes, byte_loss : int, chunk_size : int = 65536, at_location : int = 0, once : bool = True, fd  = None):
    """Adds the given bytes at a certain location of the file. Shifting is involved. Can be used to insert to the beginning of the file.

    Args:
        file_path (str): Location of the file
        given_bytes (bytes): The bytes to add

        byte_loss (int): The amount of bytes expected to be lost after adding into a certain index, e.g, 'test123' at_location 2
        with the addition of 'okay', assuming 'st' is to be replaced, then it would result in the loss of '12' (teokay3) which
        has the length of 2 and the final result must be 'teokay123'. Therefore, at the firstcall, simply calculate the amount
        of bytes to stuff - the length of what will it override. Use byte_loss = 0 if you want to overrwrite from specific place.
        Use byte_loss=len(byte_loss) to add into at_location without any loss and effectively shift the all bytes to the right.

        chunk_size (int): Chunk size to have in memory
        at_location (int, optional): Index location to start addition from. Defaults to 0.
        once (bool, optional): Boolean to mark the first iteration. MUST NOT BE USED.
        fd: FileDescriptor. MUST NOT BE USED.
    """
    print("overriding")
    if len(given_bytes) == 0:
        print("given_bytes zero quit")
        return
    tmp = get_file_size(file_path)
    if tmp[0] < 0:
        raise FileError(tmp[1])
    original_size = tmp[0]
    save_location = at_location
    if fd:
        fd.seek(at_location+(len(given_bytes) - byte_loss))
        lost_chunk = fd.read(chunk_size)
        fd.seek(at_location)
        fd.write(given_bytes)
        if once:
            fd.write(lost_chunk[:byte_loss])
        save_location = fd.tell()
    else:   # FIRST TIME TO SAVE OPEN, AS WELL AS ONCE
        with open (file_path , "rb+") as file:
            file.seek(at_location+(len(given_bytes) - byte_loss))
            lost_chunk = file.read(chunk_size)
            file.seek(at_location)
            file.write(given_bytes)
            if once:
                file.write(lost_chunk[:byte_loss])
            save_location = file.tell()
    if save_location >= original_size:
        print("save_location quit")
        return
    if once:
        override_bytes_in_file(file_path, lost_chunk[byte_loss:], byte_loss, chunk_size, save_location, False)
    else:
        override_bytes_in_file(file_path, lost_chunk, byte_loss, chunk_size, save_location, False)
    return

def header_padder(file_path : str , amount_to_pad : int) -> None:
    """Pads the header with the given amount of padding. This amount is taken from the serialized decrypted header size.

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
    override_bytes_in_file(file_path=file_path, given_bytes=pad_bytes, byte_loss=len(pad_bytes),chunk_size=65536, at_location=hdr_pad_loc)

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
