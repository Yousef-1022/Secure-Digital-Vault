

class MutableBoolean:
    """Object class type of boolean to pass around functions
    """
    def __init__(self, start_val: bool = True):
        self.__bool = start_val

    def __str__(self) -> str:
        """Returns the boolean value as str
        """
        return str(self.__bool)

    def get_value(self) -> bool:
        """Gets the boolean
        """
        return self.__bool

    def set_value(self, value: bool) -> None:
        """Sets the boolean
        """
        self.__bool = value
