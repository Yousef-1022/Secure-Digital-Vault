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

    def set_path(self, path:str) -> None:
        self.__path = path

    # Getter methods
    def get_id(self) -> int:
        return self.__id

    def get_name(self) -> str:
        return self.__name

    def get_path(self) -> str:
        return self.__path

    def get_data_created(self) -> int:
        return self.__data_created

    def get_files(self) -> list:
        return self.__files

    # TODO

    def validate_mapped_data(self, data : dict) -> bool:
        """Checks whether the passed dict represents a valid Dictionary

        Args:
            data_dict (dict): dict from the dictionaries map

        """
        expected_types = {
            "id": int,
            "name": str,
            "path": str,
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
    def determine_parent(self, path:str) -> str:
        """Gets the parent's (directory) path, e.g: /splendid/matter/ will return: /splendid/

        Returns:
            str: Parent path. / if Main directory or "None" If invalid path
        """
        if len(path) == 1 and path[0] == "/":
            return path
        parent = None
        if path.endswith('/'):
            parent = path[:-1]
        else:
            return None
        last_slash_index = parent.rfind("/")
        return parent[:last_slash_index+1]

    @staticmethod
    def determine_name(self, path:str) -> str:
        """Gets from the directory path the name, e.g: /splendid/matter/ will return: matter
        Returns:
            str: Name of the directory, "None" If invalid
        """
        if len(path) == 1 and path[0] == "/":
            return path
        name = None
        if path.endswith('/'):
            name = path[:-1]
        else:
            return name
        last_slash_index = name.rfind("/")
        result = name[last_slash_index+1:len(name)]
        if len(result) == 0:
            return None
        return result

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

