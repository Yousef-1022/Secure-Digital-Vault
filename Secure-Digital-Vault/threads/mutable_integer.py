

class MutableInteger:
    """Object class type of int to pass around functions
    """
    def __init__(self, start_val: int = 0):
        self.__int = start_val

    def __str__(self) -> str:
        """Returns the integer value as str
        """
        return str(self.__int)

    def get_value(self) -> int:
        """Gets the integer
        """
        return self.__int

    def set_value(self, value: int) -> None:
        """Sets the integer
        """
        self.__int = value
