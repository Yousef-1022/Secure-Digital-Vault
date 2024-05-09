from PyQt6.QtWidgets import QTreeWidgetItem


class CustomQTreeWidgetItem(QTreeWidgetItem):
    """Extended QTreeWidgetItem with a file_path and saved_obj. PyQt objects are ultimately C++ objects wrapped by Python.
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.__path = 0
        self.__saved_obj = None
        self.__in_vault_loc = None

    def set_path(self, given_path) -> None:
        self.__path = given_path

    def get_path(self):
        return self.__path

    def set_saved_obj(self, obj : object) -> None:
        self.__saved_obj = obj

    def get_saved_obj(self) -> object:
        return self.__saved_obj

    def set_in_vault_location(self, in_vault_loc : str):
        self.__in_vault_loc = in_vault_loc

    def get_in_vault_location(self) -> str:
        return self.__in_vault_loc
