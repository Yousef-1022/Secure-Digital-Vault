from custom_exceptions.classes_exceptions import FileDoesNotExist, MissingKeyInJson, JsonWithInvalidData
from classes.file import File


class Directory:
    def __init__(self, data_dict : dict) -> None:
        self.validate_mapped_data(data_dict)
        self.__id            = data_dict["id"]
        self.__name          = data_dict["name"]
        self.__data_created  = data_dict["data_created"]
        self.__last_modified = data_dict["last_modified"]
        self.__path          = data_dict["path"]
        self.__files         = data_dict["files"]

    def __str__(self) -> str:
        return f"{self.__name} , Total of files excluding subfolders: {len(self.__files)}"

    # Setter methods
    def set_id(self, id:int) -> None:
        self.__id = id

    def set_name(self, name:str) -> None:
        self.__name = name

    def set_path(self, path) -> None:
        """Sets the path of the directory

        Args:
            path (int|str): Path to set
        """
        self.__path = path

    def set_last_modified(self, new_date : int) -> None:
        self.__last_modified = new_date

    # Getter methods
    def get_id(self) -> int:
        return self.__id

    def get_name(self) -> str:
        return self.__name

    def get_path(self):
        """Gets the path of the directory

        Returns:
            int|str: the path of the Directory
        """
        return self.__path

    def get_data_created(self) -> int:
        return self.__data_created

    def get_last_modified(self) -> int:
        return self.__last_modified

    def get_files(self) -> list:
        return self.__files

    def get_metadata(self) -> dict:
        return {
            "name": self.__name,
            "type": "Folder",
            "data_created" : self.__data_created,
            "last_modified" : self.__last_modified,
            "files" : len(self.__files)
        }

    def get_as_dict(self) -> dict:
        return {
            "id": self.__id,
            "name": self.__name,
            "path": self.__path,
            "data_created": self.__data_created,
            "last_modified": self.__last_modified,
            "files": self.__files
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
            "last_modified": int,
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
