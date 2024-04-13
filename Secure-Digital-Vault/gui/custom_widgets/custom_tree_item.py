from PyQt6.QtWidgets import QTreeWidgetItem

class CustomQTreeWidgetItem(QTreeWidgetItem):
    """Extended QTreeWidgetItem with a file_path and saved_obj. PyQt objects are ultimately C++ objects wrapped by Python.
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.__file_path = ""
        self.__saved_obj = None

    def set_file_path(self, file_path : str) -> None:
        self.__file_path = file_path

    def get_file_path(self) -> str:
        return self.__file_path

    def set_saved_obj(self, obj : object) -> None:
        self.__saved_obj = obj

    def get_saved_obj(self) -> object:
        return self.__saved_obj
