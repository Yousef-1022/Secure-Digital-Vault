from PyQt6.QtCore import QByteArray, QFileInfo, QBuffer, QSize, QDir
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QFileIconProvider


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
    pixmap.save(buffer, "PNG", quality=1)
    byte_array = buffer.data()
    buffer.close()
    return byte_array.data()

def get_files_and_folders_paths(path : str) -> list[tuple[str,str]]:
    """Gets the files and folders in the given path

    Args:
        path (str): The path

    Returns:
        list[tuple[str,str]: All the files and folders in the given directory as a list of tuples.
        First element is the type (File or Folder), Second is the path.
    """
    result = []
    directory = QDir(path)
    directory.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.NoSymLinks)
    for entry in directory.entryInfoList():
        file_info = QFileInfo(entry)
        if file_info.isDir():
            entry_type = "Folder"
        else:
            entry_type = "File"
        data = (entry_type, entry.absoluteFilePath())
        result.append(data)
    return result

def get_amount_of_files_or_folders(path : str, subfolders : bool = True, include_files : bool = True, include_folders : bool = True):
    """Returns the amount of files and subfolders if requested in the given path using recursion

    Args:
        path (str): path to search
        subfolders (bool, optional): Include subfolders. Defaults to True.
        include_files (bool, optional): If only the TOTAL amount of files in the given path. Defaults to True.
        include_folders (bool, optional): If only the TOTAL amount folders in the given path. Defaults to True.

    Returns:
        int or Tuple[int,int]: If both options are specified to True or False, a Tuple(files,folders) is returned. Int otherwise.
    """
    if not include_files and not include_folders:
        return 0,0
    directory = QDir(path)
    directory.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.NoSymLinks)
    total_files = total_folders = 0
    for entry in directory.entryInfoList():
        if entry.isDir():
            total_folders += 1
            # Check subfolders
            if subfolders:
                folder_name = entry.baseName()
                # Iterate oversubfolders and include files
                if include_files:
                    files, folders = get_amount_of_files_or_folders(f'{path}/{folder_name}', subfolders=subfolders, include_files=True, include_folders=True)
                    total_files += files
                # Iterate oversubfolders and dont include files
                else:
                    folders = get_amount_of_files_or_folders(f'{path}/{folder_name}', subfolders=subfolders, include_files=False, include_folders=True)
                total_folders += folders
        elif include_files:
            total_files += 1
    if include_files and not include_folders:
        return total_files
    elif not include_files and include_folders:
        return total_folders
    else:
        return total_files, total_folders

def get_item_info(path : str) -> dict:
    """Creates a ready dict to insert into header based on the item. For file, id, size, loc, ico loc, checksum, path, need to be updated.
    For a directory, the id needs to be add and the amount of files. There also shouldn't be a trailing slash

    Args:
        path (str): the path on disk

    Returns:
        dict: Dictionary ready to be inserted into header. Caution: Add remaining keys of the item as per description.
    """
    res = {}
    item = QFileInfo(path)
    if item.isDir():
        res["id"] = -1
        res["name"] = item.fileName()
        res["path"] = 0
        res["data_created"] = item.birthTime().toSecsSinceEpoch()
        res["last_modified"] = item.lastModified().toSecsSinceEpoch()
        res["files"] = []
    else:
        res["id"] = -1
        res["size"] = item.size()
        res["loc_start"] = -1
        res["loc_end"] = -1
        res["checksum"] = "Unknown"
        res["file_encrypted"] = False
        res["path"] = 0
        res["metadata"] = {
            "name" : item.fileName(),
            "type" : item.completeSuffix(),
            "data_created": item.birthTime().toSecsSinceEpoch(),
            "last_modified" : item.lastModified().toSecsSinceEpoch(),
            "icon_data_start": -1,
            "icon_data_end" : -1,
            "voice_note_id" : -1
        }
    return res

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
