class File:
    """File structure used internally to represent a file within the vault
    """
    def __init__(self, file_info:dict):
        self.__id             = file_info["id"]
        self.__size           = file_info["size"]
        self.__loc_start      = file_info["loc_start"]
        self.__loc_end        = file_info["loc_end"]
        self.__checksum       = file_info["checksum"]
        self.__file_encrypted = file_info["file_encrypted"]
        self.__path           = file_info["path"]
        self.__metadata       = file_info["metadata"]

    def __str__(self):
        if ({self.__metadata["name"]} and {self.__metadata["type"]}):
            return f"File: {self.__path}{self.__metadata["name"]}{self.__metadata["type"]}, id:{self.__id}"
        return f"File: {self.__path}, id:{self.__id}"

    # Getter methods
    def get_id(self) -> int:
        return self.__id

    def get_size(self) -> int:
        return self.__size

    def get_loc_start(self) -> int:
        return self.__loc_start

    def get_loc_end(self) -> int:
        return self.__loc_end

    def get_checksum(self) -> str:
        return self.__checksum

    def get_file_encrypted(self) -> bool:
        return self.__file_encrypted

    def get_path(self) -> str:
        return self.__path

    def get_metadata(self) -> dict:
        return self.__metadata

    # Setter methods
    def set_id(self, id:int) -> None:
        self.__id = id

    def set_size(self, size:int) -> None:
        self.__size = size

    def set_loc_start(self, loc_start:int) -> None:
        self.__loc_start = loc_start

    def set_loc_end(self, loc_end:int) -> None:
        self.__loc_end = loc_end

    def set_checksum(self, checksum:str) -> None:
        self.__checksum = checksum

    def set_file_encrypted(self, file_encrypted:bool) -> None:
        self.__file_encrypted = file_encrypted

    def set_path(self, path:str) -> None:
        self.__path = path

    def set_metadata(self, metadata:dict) -> None:
        self.__metadata = metadata
