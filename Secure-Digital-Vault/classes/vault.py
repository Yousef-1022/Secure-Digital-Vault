from utils.constants import *
from utils.parsers import parse_json_safely
from utils.id_gen import gen_id
from utils.serialization import serialize_dict
from utils.helpers import count_digits

from logger.logging import Logger
from classes.file import File
from classes.directory import Directory
from classes.note import Note
from custom_exceptions.classes_exceptions import JsonWithInvalidData, MissingKeyInJson

from crypto.encryptors import encrypt_header, encrypt_footer

from file_handle.file_io import override_bytes_in_file, add_magic_into_header, header_padder, find_header_pointers, delete_footer_and_hint


class Vault:
    def __init__(self, password : str, vault_path : str):
        self.__header = {}
        self.__footer = {"error_log" : "", "session_log" : ""}
        self.__map = {}
        self.__vault_path = vault_path
        self.__password = password
        self.__hint = "No Hint"

    # Getters, Setters and Loaders
    def get_header(self) -> dict:
        """Gets the header as a dict

        Returns:
            dict: Returns the header as a whole from the Vault
        """
        return self.__header

    def set_header(self, header:dict):
        """Sets the header

        Args:
            header (dict): header to set
        """
        self.__header = header
        self.__map = self.__header["map"]

    def get_footer(self) -> dict:
        """Gets the footer as a dict

        Returns:
            dict: Returns the footer
        """
        return self.__footer


    def set_footer(self, footer:dict):
        """Sets the footer

        Args:
            footer (dict): header to set
        """
        self.__footer = footer

    def add_error_log_to_footer(self, msg : str):
        """Adds an error log the footer

        Args:
            msg (str): The log message
        """
        self.__footer["error_log"] += msg

    def add_normal_log_to_footer(self, msg : str):
        """Adds a normal log the footer

        Args:
            msg (str): The log message
        """
        self.__footer["session_log"] += msg

    def request_footer_and_hint_delete(self, footer_start : int):
        """Deletes the footer and its MAGIC along with the hint

        Args:
            footer_start (int): Location of the footer start after the magic bytes
        """
        if footer_start > 0:
            delete_footer_and_hint(self.__vault_path, footer_start)

    def refresh_header(self, return_it : bool = False) -> bytes:
        """Refreshes the header size and has an optional value to return the header.

        Args:
            return_it (bool) optional: choice to to return the header or not

        Returns:
            bytes: serialized new header, but not encrypted
        """
        # Other data is updated in real time, we only need to update the size.
        old_header_serialized = serialize_dict(self.__header)
        old_header_len = self.__header["vault"]["header_size"]
        old_digits = count_digits(old_header_len)
        new_header_len = len(old_header_serialized)
        new_digits = count_digits(new_header_len)
        self.__header["vault"]["header_size"] = new_header_len + (new_digits - old_digits)
        new_header_serialized = serialize_dict(self.__header)
        if return_it:
            return new_header_serialized
        return None

    def get_password(self) -> str:
        """Gets the decrypted password of the vault.

        Returns:
            str: The password as a string.
        """
        return self.__password

    def set_password(self, password : str) -> None:
        """Sets the password of the vault with the given string.

        Args:
            password (str): The password as a string
        """
        self.__password = password

    def get_hint(self) -> str:
        """Gets the password hint of the vault.

        Returns:
            str: The hint as a string.
        """
        return self.__hint

    def set_hint(self, hint : str) -> None:
        """Sets the hint of the vault with the given string.

        Args:
            password (str): The password as a string
        """
        self.__hint = hint

    def get_map(self) -> dict:
        """Returns the map of the vault as a dict

        Returns:
            dict: The map as a dict
        """
        return self.__map

    def set_map(self, map:dict):
        """Sets the map

        Args:
            map (dict): map to set
        """
        self.__map = map

    def get_vault_path(self) -> str:
        """Returns the path of the saved Vault File.

        Returns:
            str: The file (vault) location on Disk
        """
        return self.__vault_path

    def set_vault_path(self, new_path : str):
        """Sets the vault path to the new location on the Disk

        Args:
            new_path (str): The absolute path on the disk
        """
        self.__vault_path = new_path

    def get_vault_size(self) -> int:
        """Returns the UNENCRYPTED header_size of the Vault

        Returns:
            int: The length of the the unencrypted seralized header of the Vault.
        """
        return self.__header["vault"]["header_size"]

    def get_vault_details(self) -> dict:
        """Returns the vault details 'vault'

        Returns:
            dict: The dict of the 'vault'
        """
        return self.__header["vault"]

    def determine_if_dir_path_is_valid(self, dir_names : list, level : int = 0) -> tuple[bool,int]:
        """Based on the name of a dir, tries to determine whether it is a valid path,
        this function works in harmony with: parse_directory_string

        Args:
            dir_names (list): A list containing all the dir names, e.g, [path,to,somewhere] generated by parse_directory_string
            level (int): current level of directory, e.g, /path/to/somewhere path is 1 , to is 2 , somewhere is 3

        Returns:
            tuple: first part if valid, second part showing the last level
        """
        data_dict = self.get_map()["directories"]
        length = len(dir_names)
        if length < 1:
            return True,level
        elif length == 1 and dir_names[0] == "/":
            return True,0
        else:
            for some_dir in data_dict.values():
                if dir_names[0] == some_dir["name"] and some_dir["path"] == level:
                    return self.determine_if_dir_path_is_valid(dir_names[1:], some_dir["id"])
        return False,level

    @staticmethod
    def determine_directory_path(path_id: int, data_dict: dict, current_name: str = None) -> str:
        """Based on the path id , returns the full path name representing the id, e.g: for 2: 'id2 = matter , id1 = splendid' will return: /splendid/matter/
            This is done recursively, and the given data_dict must be valid. (This is checked beforehand)
        Args:
            path_id (int): path id of the directory
            data_dict (dict): dict containing all the dictionaries
            current_name(str) optional: name of folder.

        Returns:
            str: Name of the directory, "/" If path <= 0
        """
        if path_id <= 0:
            if current_name is None:
                return "/"
            return f"/{current_name}/"

        if str(path_id) not in data_dict:
            if current_name is None:
                return "/"
            return f"/{current_name}/"

        parent_name = data_dict[str(path_id)]["name"]

        if current_name is not None:
            parent_name += f"/{current_name}"

        parent_id = data_dict[str(path_id)]["path"]
        return Vault.determine_directory_path(parent_id, data_dict, parent_name)

    def __insert_file_id(self, file_id : int):
        """Internal function used after the id generation.

        Args:
            file_id (int): The newly generted id by gen_id. (A function must call self.generate_id)
        """
        self.__map["file_ids"].append(file_id)

    def insert_file(self, file_dict : dict):
        """Inserts the given file dict into the header. This must be called after physically appending the file into the vault

        Args:
            file_dict (dict): The file dict into the header.
        """
        self.__map["files"][str(file_dict["id"])] = file_dict
        size = file_dict["size"]
        self.__header["vault"]["file_size"] += size
        self.__header["vault"]["amount_of_files"] += 1

    def remove_file(self, file_id : int):
        """Removes the given file id from: the map, file_ids , the directory it belongs to, and decreases the amount of files.
        This function should be called after physically removing the file id from the vault.

        Args:
            file_id (int): The file id to remove from the header
        """
        folder_id = self.__map["files"][str(file_id)]["path"]
        self.__map["file_ids"].remove(file_id)
        if folder_id > 0:
            self.__map["directories"][str(folder_id)]["files"].remove(file_id)
        self.__map["files"].pop(str(file_id))
        self.__header["vault"]["amount_of_files"] -= 1

    def insert_file_id_into_folder(self, folder_id : int , file_id : int):
        """Inserts the given file id, which has its path as "folder_id" already defined into the folder.

        Args:
            folder_id (int): The folder which should the file_id be inside.
            file_id (int): The file id (dict) of which its path is already set to "folder_id"
        """
        if folder_id > 0:
            self.__map["directories"][str(folder_id)]["files"].append(file_id)

    def __insert_folder_id(self, folder_id : int):
        """Internal function used after the id generation.

        Args:
            folder_id (int): The newly generted id by gen_id. (A function must call self.generate_id)
        """
        self.__map["directory_ids"].append(folder_id)

    def remove_folder(self, folder_id : int):
        """Removes the given folder id from: the map, directory_ids , and clears any file ids in it.

        Args:
            folder_id (int): The folder id to remove from the header
        """
        if folder_id > 0:
            self.__map["directory_ids"].remove(folder_id)
            self.__map["directories"][str(folder_id)]["files"].clear()
            self.__map["directories"].pop(str(folder_id))

    def insert_folder(self, folder_dict : dict):
        """Inserts the given folder dict into the header. No need for byte allocation after the header.

        Args:
            file_dict (dict): The folder dict into the header.
        """
        self.__map["directories"][str(folder_dict["id"])] = folder_dict

    def __insert_note_id(self, note_id : int):
        """Internal function used after the id generation.

        Args:
            note_id (int): The newly generted id by gen_id. (A function must call self.generate_id)
        """
        self.__map["note_ids"].append(note_id)

    def insert_note(self, note_dict : dict):
        """Inserts the given note dict into the header. This must be called after physically appending the note into the vault

        Args:
            note_dict (dict): The note dict into the header.
        """
        self.__map["notes"][str(note_dict["id"])] = note_dict
        self.__map["files"][str(note_dict["owned_by_file"])]["metadata"]["note_id"] = note_dict["id"]
        self.__map["files"][str(note_dict["owned_by_file"])]["metadata"]["last_modified"] = Logger.get_current_time()
        note_size = note_dict["loc_end"] - note_dict["loc_start"]
        self.__header["vault"]["file_size"] += note_size
        self.__header["vault"]["amount_of_files"] += 1 # Counts as a File

    def remove_note(self, note_id : int):
        """Removes the given note id from: the map, note_ids , the file it is owned by, and decreases the amount of files

        Args:
            note_id (int): The note id to remove from the header
        """
        owned_by = self.__map["notes"][str(note_id)]["owned_by_file"]
        self.__map["files"][str(owned_by)]["metadata"]["note_id"] = -1
        self.__map["files"][str(owned_by)]["metadata"]["last_modified"] = Logger.get_current_time()
        self.__map["note_ids"].remove(note_id)
        self.__map["notes"].pop(str(note_id))
        self.__header["amount_of_files"] -= 1 # Counts as a File

    # Header Validators
    def validate_header(self, full_header:bytes) -> dict:
        """Validates the full header represented in bytes

        Args:
            full_header (bytes): Full header representation in bytes

        Raises:
            JsonWithInvalidData: Incase the header contains invalid data
            MissingKeyInJson: Incase there is a missing key within the inner values of the header

        Returns:
            dict: the header without magic bytes
        """
        header = parse_json_safely(full_header)
        if("error" in header):
            raise JsonWithInvalidData(str(header["error"]))
        if (self.__validate_header_keys(header)): # Can raise MissingKeyInJson or JsonWithInvalidData
            return header
        raise JsonWithInvalidData(f"JSON has incorrect magic bytes. Obj len: {len(full_header)}, Obj: {str(full_header)}")

    def __validate_header_keys(self, header: dict) -> bool:
        """Validates the full header of the vault. (vault + map)

        Args:
            header (dict): the whole header containing all keys

        Raises:
            MissingKeyInJson: Indicating that a key does not exist
            JsonWithInvalidData: Indicating that a value is of incorrect type

        Returns:
            bool: Upon success
        """
        for key in ["vault", "map"]:
            if key not in header:
                raise MissingKeyInJson(f"Key '{key}' is missing from the Vault main header.")

        self.__validate_vault_keys(header["vault"])
        self.__validate_map_keys(header["map"])

        return True

    def __validate_vault_keys(self, vault : dict) -> None:
        """Checks if the key 'vault' contains valid keys.

        Args:
            vault (dict): the dict of the the 'vault' key
        """
        for key in VAULT_KEYS:
            if key not in vault:
                raise MissingKeyInJson(f"Key '{key}' is missing from the 'vault' header.")
            if key == "vault_name" or key == "vault_extension":
                try:
                    if not isinstance(vault[key], str):
                        raise JsonWithInvalidData(f"Value for key '{key}' must be a string but '{vault[key]}' is of type: {type(vault[key])}.")
                except KeyError:
                        raise MissingKeyInJson(f"Key '{key}' does not exist in the 'vault' dict!")
            elif key == "is_vault_encrypted":
                try:
                    if not isinstance(vault[key], bool):
                        raise JsonWithInvalidData(f"Value for key 'is_vault_encrypted' must be a boolean but '{vault[key]}' is of type: {type(vault[key])}.")
                except KeyError:
                    raise MissingKeyInJson("Key 'is_vault_encrypted' does not exist in the 'vault' dict!")
            else:
                try:
                    if not isinstance(vault[key], int):
                        raise JsonWithInvalidData(f"Value for key '{key}' must be an integer but '{vault[key]}' is of type: {type(vault[key])}.")
                except KeyError:
                    raise MissingKeyInJson(f"Key '{key}' does not exist in the 'vault' dict!")

    def __validate_map_keys(self, map : dict) -> None:
        """Checks if the key 'map' contains valid keys, but does not check the correctness of files, directories, notes

        Args:
            map (dict): the dict of the the 'map' key
        """
        for key in MAP_KEYS:
            if key not in map:
                raise MissingKeyInJson(f"Key '{key}' is missing from the 'map' dict")
            # file_ids , directory_ids, note_ids
            if key[-3:] == "ids":
                try:
                    if not isinstance(map[key], list):
                        raise JsonWithInvalidData(f"Value for key '{key}' must be a list but '{map[key]}' is of type: {type(map[key])}.")
                    else:
                        for value in map[key]:
                            if not isinstance(value, int):
                                raise JsonWithInvalidData(f"The'{key}' must contain a list of integers but '{value}' is of type: {type(value)}.")
                except KeyError:
                        raise MissingKeyInJson(f"Key '{key}' does not exist in the 'map' dict!")
            # files, directories, notes
            else:
                try:
                    if not isinstance(map[key], dict):
                        raise JsonWithInvalidData(f"Value for key '{key}' must be a dict but '{map[key]}' is of type: {type(map[key])}.")
                    else:
                        for value in map[key]:
                            if not isinstance(value, str):
                                raise JsonWithInvalidData(f"The '{key}' key must be a str (id) only, but '{value}' is of type: {type(value)}.")
                        for value in map[key].values():
                            if not isinstance(value, dict):
                                raise JsonWithInvalidData(f"The '{key}' key must be of type dict only, but '{value}' is of type: {type(value)}.")
                except KeyError:
                    raise MissingKeyInJson(f"Key '{key}' does not exist in the 'map' dict!")

    def validate_footer(self, full_footer:bytes) -> dict:
        """Validates the full footer represented in bytes

        Args:
            full_footer (bytes): Full footer representation in bytes

        Raises:
            JsonWithInvalidData: Incase the footer contains invalid data
            MissingKeyInJson: Incase there is a missing key within the inner values of the footer

        Returns:
            dict: the footer without magic bytes
        """
        footer = parse_json_safely(full_footer)
        if("error" in footer):
            raise JsonWithInvalidData(str(footer))
        if (self.__check_footer_keys(footer)): # Can raise MissingKeyInJson
            return footer
        raise JsonWithInvalidData(f"JSON has incorrect magic bytes. Obj len: {len(full_footer)}, Obj: {str(full_footer)}")

    def __check_footer_keys(self, footer:dict) -> bool:
        for key in FOOTER_KEYS:
            if key not in footer.keys():
                raise MissingKeyInJson(f"Key: {key} is missing from the Vault Footer.")
        return True

    def update_vault_file(self):
        """Updates the vault with the newly encrypted header, and updates the disk.
        This function should only be called after adding the relevant items into the vault, as it
        shifts the location of everything. This function should be called by a thread.
        """
        header = self.refresh_header(return_it=True)
        header = encrypt_header(self.get_password(), header)
        encrypted_header_len = len(header)
        header = add_magic_into_header(header, start_only=True, pad_only=True, end_only=False)

        res = find_header_pointers(self.__vault_path)
        available_padding = res[0]
        header_on_disk_size = res[1]

        # If new header is smaller than what is on the disk, zeroize the MAGIC_HEADER_PAD
        if encrypted_header_len < header_on_disk_size:
            fd = override_bytes_in_file(file_path=self.__vault_path, given_bytes=bytes([0] * 8), byte_loss=0, at_location=res[3])
            if fd:
                fd.close()
        # If new header is bigger than what is on the disk
        elif (header_on_disk_size+available_padding) <= (encrypted_header_len+32): # 32 extra bytes to account for magic
            to_pad = abs((encrypted_header_len+32) - (header_on_disk_size+available_padding)) + VAULT_BUFFER_LIMIT
            self.data_index_shifter(shift_by=to_pad, shift_direction=True, at_index=-1)
            header_padder(file_path=self.__vault_path, amount_to_pad=to_pad)
            # Need to account for extra digit length by data_index_shifter, thus must to re-encrypt header:
            header = self.refresh_header(return_it=True)
            header = encrypt_header(self.get_password(), header)    # Cannot avoid encrypting twice for now.
            header = add_magic_into_header(header, start_only=True, pad_only=True, end_only=False)
        fd = override_bytes_in_file(file_path=self.__vault_path, given_bytes=header, byte_loss=0, at_location=0)
        if fd:
            fd.close()

    def generate_id(self, type : str) -> int:
        """Generates a new ID for either a new file or a new folder or a new note

        Args:
            type (str): F for File, D for Folder, V for Note

        Returns:
            int: The new id

        Throws: ClashedIdException
        """
        the_id = -1
        if type == "F":
            the_id = gen_id(self.__map["file_ids"] , "file_ids")
            self.__insert_file_id(the_id)
        elif type == "D":
            the_id = gen_id(self.__map["directory_ids"], "directory_ids")
            self.__insert_folder_id(the_id)
        elif type == "V":
            the_id = gen_id(self.__map["note_ids"], "note_ids")
            self.__insert_note_id(the_id)
        return the_id

    def data_index_shifter(self, shift_by : int, shift_direction : bool, at_index : int = -1) :
        """Shifts the data in the header by a given a number. This includes: File location, Note location, and Icon Location.

        Args:
            shift_by (int): Amount of bytes to shift by.
            shift_direction (bool): True if to the right (add), False if to the Left (Subtract)
            at_index (int): Shift only those after this index.
        """
        # Shifting files and their icons locations
        for f_id in self.__map["files"].keys():

            proceed_file = True
            proceed_icon = True

            if at_index != -1:
                # If shift to the right (after append override), that means the loc_start must be less than the index to be update
                if self.__map["files"][f_id]["loc_start"] <= at_index:
                    proceed_file = False
                if self.__map["files"][f_id]["metadata"]["icon_data_start"] <= at_index:
                    proceed_icon = False

            if proceed_file:
                if shift_direction:
                    self.__map["files"][f_id]["loc_start"] += shift_by
                    self.__map["files"][f_id]["loc_end"]   += shift_by
                else:
                    self.__map["files"][f_id]["loc_start"] -= shift_by
                    self.__map["files"][f_id]["loc_end"]   -= shift_by

            if proceed_icon:
                icon_start = self.__map["files"][f_id]["metadata"]["icon_data_start"]
                icon_end = self.__map["files"][f_id]["metadata"]["icon_data_end"]
                if (icon_start > 0) and (icon_end > 0):
                    if shift_direction:
                        self.__map["files"][f_id]["metadata"]["icon_data_start"] += shift_by
                        self.__map["files"][f_id]["metadata"]["icon_data_end"]   += shift_by
                    else:
                        self.__map["files"][f_id]["metadata"]["icon_data_start"] -= shift_by
                        self.__map["files"][f_id]["metadata"]["icon_data_end"]   -= shift_by

        # Shifting note notes location
        for v_id in self.__map["notes"].keys():

            proceed = True

            if at_index != -1:
                if self.__map["notes"][v_id]["loc_start"] <= at_index:
                    proceed = False

            if proceed:
                if shift_direction:
                    self.__map["notes"][v_id]["loc_start"] += shift_by
                    self.__map["notes"][v_id]["loc_end"]   += shift_by
                else:
                    self.__map["notes"][v_id]["loc_start"] -= shift_by
                    self.__map["notes"][v_id]["loc_end"]   -= shift_by

    def get_files_with(self, name : str, extension : str, match_case : bool, is_encrypted : bool, has_note : bool) -> list[dict]:
        """Gets the files with the given description from the vault.

        Args:
            name (str): File name, can be empty to find by case only
            extension (str): File extension
            match_case (bool): Match case of the file name
            is_encrypted (bool): Grab file according to value
            has_note (bool): Choose file if True

        Returns:
            list[dict]: A list of dicts representing files that belong into the the map
        """
        res = []
        for f in self.__map["files"].values():
            # Name check, Fall through if empty
            if name != '':
                if match_case and not (name == f["metadata"]["name"]):
                    continue
                elif not (name.lower() in f["metadata"]["name"].lower()):
                    continue
            # Extension check. Stored extension doesn't contain the dot. Fall through if empty
            if extension != '':
                if f["metadata"]["type"] != extension[1:]:
                    continue
            # Encryption check. Fall through if empty
            if is_encrypted and f["file_encrypted"] == False:
                continue
            # Note check.
            if has_note and f["metadata"]["note_id"] == -1:
                continue
            res.append(f)
        return res

    def get_id_from_vault(self, the_id : int, type : str, as_dict : bool = True) -> tuple[bool,object]:
        """Gets the ID from the vault.

        Args:
            the_id (int): The ID to look for
            type (str): F for File, D for Folder, V for Note
            as_dict (bool): Whether to keep the item as a dict, or as a class

        Returns:
            tuple[bool,object]: first part if exists, second part the actual dict or item
        """
        res = (False, f'ID: {the_id} of type {type} doe not exist!')
        if type == "F":
            if the_id in self.__map["file_ids"]:
                if as_dict:
                    res = (True, self.__map["files"][str(the_id)])
                else:
                    res = (True, File(self.__map["files"][str(the_id)]))
        elif type == "D":
            if the_id in self.__map["directory_ids"]:
                if as_dict:
                    res = (True,self.__map["directories"][str(the_id)])
                else:
                    res = (True, Directory(self.__map["directories"][str(the_id)]))
        elif type == "V":
            if the_id in self.__map["note_ids"]:
                if as_dict:
                    res = (True, self.__map["notes"][str(the_id)])
                else:
                    res = (True, Note(self.__map["notes"][str(the_id)]))
        return res

    def get_name_of_id(self, the_id : int, type : str) -> str:
        """Gets the name of the given id

        Args:
            the_id (int): The id to look for
            ttype (str): F for File, D for Folder

        Returns:
            str: Name of the id
        """
        res = ''
        if type == "F":
            if the_id in self.__map["file_ids"]:
                res = self.__map["files"][str(the_id)]["metadata"]["name"]
        elif type == "D":
            if the_id in self.__map["directory_ids"]:
                res = self.__map["directories"][str(the_id)]["name"]
        return res

    def get_full_path(self, the_id: int) -> str:
        """Gets the full path of the given folder id

        Args:
            the_id (int): The folder id to get its full path.

        Returns:
            str: Full path, e.g /path/to/
        """
        return Vault.determine_directory_path(the_id, self.__map["files"])

    def get_files_belonging_in_id(self, folder_id : int, get_path_as_int : bool = True, parent_folder_name : str = None) -> list[File]:
        """Gets all the files existing in the given folder id, this includes subfolders

        Args:
            folder_id (int): The id of the folder
            get_path_as_int (bool) optional: Whether to keep the File path as default, or Path id. If False, it overrides the set_path to a str of path
            parent_folder_name (str) optional: To add the parent folder name into the already available path

        Returns:
            list[File]: List of File class
        """
        # Files:
        file_list = self.__map["directories"][str(folder_id)]["files"]
        files = []
        for file_id in file_list:
            f = File(self.__map["files"][str(file_id)])
            if not get_path_as_int:
                path_to_set = f'{parent_folder_name+"/" if parent_folder_name else "/"}'
                f.set_path(path_to_set)
            files.append(f)

        # Folders:
        if folder_id in self.__map["directory_ids"]:
            for folder in self.__map["directories"].values():
                if folder["path"] == folder_id:
                    res = self.get_files_belonging_in_id(folder["id"], get_path_as_int, f'{parent_folder_name+"/" if parent_folder_name else ""}{folder["name"]}')
                    files.extend(res)
        return files

    def get_items_under_id(self, belong_to : int) -> list:
        """Returns the items which belong to the id

        Args:
            belong_to (int): The id which items belong to its path

        Returns:
            list: List of Files and Directories
        """
        lst = []
        # Check Directories first
        for some_folder in self.__map["directories"].values():
            if some_folder["path"] == belong_to:
                dict = Directory(some_folder)
                lst.append(dict)
        for some_file in self.__map["files"].values():
            if some_file["path"] == belong_to:
                file = File(some_file)
                lst.append(file)
        return lst

    def update_file_in_vault(self, file : File):
        """Updates a certain file in the vault. This file is checked.

        Args:
            file (File): The checked File
        """
        self.__map["files"][str(file.get_id())] = file.get_as_dict()

    def update_folder_in_vault(self, folder : Directory):
        """Updates a certain folder in the vault. This folder is checked.

        Args:
            folder (Directory): The checked Directory
        """
        self.__map["directories"][str(folder.get_id())] = folder.get_as_dict()

    def safe_remove_folder(self, folder_id : int) -> tuple[bool,str]:
        """Safely removes the folder id from the vault without deleting any files.

        Args:
            folder_id (int): The folder id to remove

        Returns:
            tuple[bool,str]: First value whether it was successful, second value if something went wrong
        """
        if folder_id == 0:
            return True, ""
        try:
            files = len(self.__map["directories"][str(folder_id)]["files"])
            name = self.__map["directories"][str(folder_id)]["name"]
            if files != 0:
                return False, f"Folder {name} has {files} inside! Thus, cannot remove"
            self.remove_folder(folder_id)
        except KeyError:
            return False, f"The folder id {folder_id} does not exist!"
        except ValueError:
            return True, f"The folder id {folder_id} exists and was removed, but it wasnt in the directory_ids"
        return True, ""

    def update_file_size_of_vault(self, amount_of_bytes : int):
        """Updates the header's 'file_size' with the given variable

        Args:
            amount_of_bytes (int): amount of bytes to update with
        """
        self.__header["vault"]["file_size"] += amount_of_bytes

    def update_item_index(self, the_id : int , start_loc : int, end_loc : int , type : str):
        """Updates the item location index

        Args:
            the_id (int): The ID of the item
            start_loc (int): New Start Location
            end_loc (int): New End Location
            type (str): The type of item, V for note, F for File
        """
        if type == "F":
            self.__map["files"][str(the_id)]["loc_start"] = start_loc
            self.__map["files"][str(the_id)]["loc_end"] = end_loc
        elif type == "V":
            self.__map["notes"][str(the_id)]["loc_start"] = start_loc
            self.__map["notes"][str(the_id)]["loc_end"] = end_loc

    def generate_footer(self) -> bytes:
        """Generates a footer which is encrypted with the current password

        Returns:
            bytes: The footer as encrypted bytes
        """
        the_footer = serialize_dict(self.__footer)
        the_footer = encrypt_footer(self.__password, the_footer)
        return the_footer

    def get_last_related_idx(self) -> int:
        """Returns the last idx the vault is tracking of

        Returns:
            int: The last idx the vault is tracking of
        """
        biggest_idx = 0
        for f_id in self.__map["files"].keys():
            icon_end = self.__map["files"][f_id]["metadata"]["icon_data_end"]
            file_end = self.__map["files"][f_id]["loc_end"]
            if icon_end > file_end:
                if biggest_idx < icon_end:
                    biggest_idx = icon_end
            else:
                if biggest_idx < file_end:
                    biggest_idx = file_end

        for n_id in self.__map["notes"].keys():
            note_end = self.__map["notes"][n_id]["loc_end"]
            if biggest_idx < note_end:
                biggest_idx = note_end
        return biggest_idx
