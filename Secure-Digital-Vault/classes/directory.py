from custom_exceptions.classes_exceptions import FileDoesNotExist
from file import File


class Directory:
    def __init__(self, id:int, name:str, path:str) -> None:
        self.__id   = id
        self.__name = name
        self.__path = path
        self.__files  = []

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

    def determine_parent(self) -> int:
        """Gets the parent's (directory) id

        Returns:
            int: Parent id. -1 if Main directory, another number if not Main directory.
        """
        if (self.__path == "/"):
            return -1
        last_slash_index = self.__path.rfind("/")
        second_last_slash_index = self.__path.rfind("/", 0, last_slash_index)
        parent_id = int(self.__path[second_last_slash_index + 1:last_slash_index])
        return parent_id

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

