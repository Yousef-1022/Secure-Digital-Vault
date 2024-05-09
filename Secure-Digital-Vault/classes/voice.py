

class Voice:
    """Note structure used internally to represent a note within the vault
    """
    def __init__(self, note_id : int, owned_by : int, start_loc : int, end_loc : int, extension : str, checksum : str):
        self.__id        = note_id
        self.__owned_by  = owned_by
        self.__loc_start = start_loc
        self.__loc_end   = end_loc
        self.__extension = extension
        self.__checksum  = checksum

    def get_id(self) -> int:
        return self.__id

    def set_id(self, the_id : int) -> None:
        self.__id = the_id

    def get_owned_by(self) -> int:
        return self.__owned_by

    def set_owned_by(self, file_id : int) -> None:
        self.__owned_by = file_id

    def get_loc_start(self) -> int:
        return self.__loc_start

    def set_loc_start(self, loc_start : int) -> None:
        self.__loc_start = loc_start

    def get_loc_end(self) -> int:
        return self.__loc_end

    def set_loc_end(self, loc_end:int) -> None:
        self.__loc_end = loc_end

    def get_extension(self) -> str:
        return self.__extension

    def set_extension(self, extension : str) -> None:
        self.__extension = extension

    def get_checksum(self) -> str:
        return self.__checksum

    def set_checksum(self, checksum : str) -> None:
        self.__checksum = checksum

    def get_dict(self) -> dict:
        """Returns a dict in the map format

        Returns:
            dict: The dict to add into the map
        """
        return {
            "id" : self.__id,
            "owned_by_file" : self.__owned_by,
            "loc_start" : self.__loc_start,
            "loc_end" : self.__loc_end,
            "checksum" : self.__checksum
        }
