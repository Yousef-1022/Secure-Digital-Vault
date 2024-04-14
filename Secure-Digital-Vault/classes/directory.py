from custom_exceptions.classes_exceptions import FileDoesNotExist, MissingKeyInJson, JsonWithInvalidData
from classes.file import File


class Directory:
    def __init__(self, data_dict : dict) -> None:
        self.validate_mapped_data(data_dict)
        self.__id           = data_dict["id"]
        self.__name         = data_dict["name"]
        self.__data_created = data_dict["data_created"]
        self.__path         = data_dict["path"]
        self.__files        = data_dict["files"]

    # Setter methods
    def set_id(self, id:int) -> None:
        self.__id = id

    def set_name(self, name:str) -> None:
        self.__name = name

    def set_path(self, path:int) -> None:
        self.__path = path

    # Getter methods
    def get_id(self) -> int:
        return self.__id

    def get_name(self) -> str:
        return self.__name

    def get_path(self) -> int:
        return self.__path

    def get_data_created(self) -> int:
        return self.__data_created

    def get_files(self) -> list:
        return self.__files

    def get_metadata(self) -> dict:
        return {
            "name": self.__name,
            "type": "Folder",
            "data_created" : self.__data_created,
            "files" : len(self.__files)
        }

    def validate_mapped_data(self, data : dict) -> bool:
        """Checks whether the passed dict represents a valid Dictionary

        Args:
            data_dict (dict): dict from the dictionaries map

        """
        expected_types = {
            "id": int,
            "name": str,
            "path": int,
            "data_created": int,
            "files": list
        }

        for key, expected_type in expected_types.items():
            if key not in data:
                raise MissingKeyInJson(f"Key: '{key}' is missing from the dict map data")
            if not isinstance(data[key], expected_type):
                raise JsonWithInvalidData(f"Key: '{key}' with data: '{data[key]}' should be of type {expected_type} but is of type: '{type(data[key])}'")
            if key == "files":
                for value in data[key]:
                    if not isinstance(value, int):
                        raise JsonWithInvalidData(f"The '{key}' key must contain a list of int but '{value}' is of type: {type(value)}.")

    @staticmethod
    def determine_parent_by_id(path_id : int , data_dict: dict) -> int:
        """Based on the path id, returns the parent id

        Args:
            path_id (int): path id of the directory you want its parent
            data_dict (dict): dict containing all the dictionaries

        Returns:
            int: Parent ID
        """
        if path_id > 0:
            for value in data_dict.values():
                if value["id"] == path_id:
                    return value["path"]
        return 0

    @staticmethod
    def determine_directory_path(path_id: int, data_dict: dict, current_name: str = None) -> str:
        """Based on the path id , returns the full path name representing the id, e.g: for 2: 'id2 = matter , id1 = splendid' will return: /splendid/matter/
            This is done recursively, and the given data_dict must be valid. (This is checked beforehand)
        Args:
            path_id (int): path id of the directory
            data_dict (dict): dict containing all the dictionaries

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
        return Directory.determine_directory_path(parent_id, data_dict, parent_name)

    @staticmethod
    def determine_if_dir_path_is_valid(dir_names : list, data_dict: dict, level : int = 0) -> tuple[bool,int]:
        """Based on the name of a dir, tries to determine whether it is a valid path,
        this function works in harmony with: parse_directory_string

        Args:
            dir_names (list): A list containing all the dir names, e.g, [path,to,somewhere]
            data_dict (dict): dict containing all the dictionaries
            level (int): current level of directory, e.g, /path/to/somewhere path is 1 , to is 2 , somewhere is 3

        Returns:
            tuple: first part if valid, second part showing the last level
        """
        length = len(dir_names)
        if length < 1:
            return True,level
        elif length == 1 and dir_names[0] == "/":
            return True,0
        else:
            for some_dir in data_dict.values():
                if dir_names[0] == some_dir["name"] and some_dir["path"] == level:
                    return Directory.determine_if_dir_path_is_valid(dir_names[1:], data_dict, some_dir["id"])
        return False,level

    def add_file(self, file:File) -> bool:
        """Adds the given file into the dictionary.

        Args:
            file (File): file object

        Returns:
            bool: True if addition was ok. False if file already exists.
        """
        for f in self.__files:
            if f.get_id() == file.get_id():
                return False
        self.__files.append(file)
        return True

    def remove_file(self, file:File) -> bool:
        """Removes the given file from the dictionary.

        Args:
            file (File): file object

        Raises:
            FileDoesNotExist: if the file does not exist

        Returns:
            bool: True if addition was ok. Else, an exception is raised.
        """
        for f in self.__files:
            if f.get_id() == file.get_id():
                self.__files.remove(f)
                return True
        raise FileDoesNotExist(f"File with id {file.get_id()} does not exist in directory {self.__name}")

