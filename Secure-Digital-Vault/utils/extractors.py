from PyQt6.QtCore import QByteArray, QFileInfo, QBuffer, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QFileIconProvider


def find_magic(vault_path: str, magic_bytes: bytes, start_from_index: int = -1, read_reverse: bool = False, chunk_size: int = 4096) -> int:
    """Finds the magic bytes in existing in the given vault_path. It is required to remove the length of the end magic bytes after caluclating
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


def get_file_from_vault(vault_path:str, starting_byte:int , ending_byte: int, chunk_size_to_read:int=4096):
    """Gets raw bytes from vault location on machine

    Args:
        vault_path (str): vault location on disk
        starting_byte (int): file start byte
        ending_byte (int): file end byte
        chunk_size_to_read(int): optional int parameter to determine the amount of chunks to read per file
    """
    with open(vault_path, "rb") as file:
        file_size = ending_byte - starting_byte
        raw_data = b''
        file.seek(starting_byte)
        if file_size > chunk_size_to_read:
            bytes_read = 0
            while bytes_read < file_size:
                chunk_size = min(chunk_size_to_read, file_size - bytes_read)
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                raw_data += chunk
                bytes_read += len(chunk)
        else:
            raw_data = file.read(ending_byte - starting_byte)
    return raw_data


def get_icon_from_file(file_loc : str) -> bytes:
    """Gets the icon from the given file and returns its pixelmap as raw bytes.
    WARNING: This function can only be used with the presence of QApplication.

    Args:
        file_loc (str): File location on the disk

    Returns:
        bytes: Raw bytes representing the pixelmap associated with the file. None if couldn't extract icon
    """
    file_info = QFileInfo(file_loc)
    file_icon_provider = QFileIconProvider()
    icon = file_icon_provider.icon(file_info)
    if icon.isNull():
        return None
    pixmap = QPixmap(icon.pixmap(icon.actualSize(QSize(256, 256)))) # Approximate Windows Platform Size.
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    byte_array = buffer.data()
    buffer.close()
    return byte_array.data()


def extract_icon_from_bytes(icon_bytes : bytes) -> QIcon:
    """Extracts QIcon saved in bytes, these bytes must be decoded first.

    Args:
        icon_bytes (bytes): bytes representing a QIcon pixelmap

    Returns:
        QIcon: the icon's pixel map saved in QIcon
    """

    pixmap_bytes = QByteArray(icon_bytes)
    final_pixmap = QPixmap()
    final_pixmap.loadFromData(pixmap_bytes)
    return QIcon(final_pixmap)

