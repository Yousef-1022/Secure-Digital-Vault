from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QStatusBar, QMessageBox
from PyQt6.QtGui import QIcon

from utils.constants import ICON_1
from utils.parsers import parse_directory_string
from crypto.utils import get_checksum
from file_handle.file_io import append_bytes_into_file

from classes.vault import Vault
from classes.voice import Voice
from custom_exceptions.classes_exceptions import MissingKeyInJson, JsonWithInvalidData
from logger.logging import Logger

from gui.custom_widgets.custom_tree_widget import CustomTreeWidget
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_messagebox import CustomMessageBox
from gui.interactions.find_file_dialog import FindFileDialog
from gui.interactions.view_file_window import ViewFileWindow
from gui.interactions.add_file_window import AddFileWindow


class VaultViewWindow(QMainWindow):
    # Settings of the vault, to change password, view vault details, get logs, decrypt vault entirely.
    def __init__(self, header : bytes, password : str, vault_path : str):
        """VaultViewWindow

        Args:
            header (bytes): Extracted Header, Then Decrypted, Then passed as bytes. {Decide if encoding place a role}
            password (str): The given password, Non Encryted
        """
        super().__init__()

        # Window Data
        self.logger = Logger()
        self.threads = []
        self.__vault = Vault(password, vault_path)
        try:
            self.__vault.set_header(self.__vault.validate_header(header))
        except MissingKeyInJson as e:
            print(e) # TODO
        except JsonWithInvalidData as e:
            print(e) # TODO

        # Windows Data
        self.__add_file_window = None

        # Interface
        self.setObjectName("VaultViewWindow")
        self.setWindowTitle("Vault View Window")
        self.setWindowIcon(QIcon(ICON_1))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.resize(1024, 768)

        # Window References are kept , they go out of scope and are garbage collected, which will destroy the underlying C++ obj.
        self.__view_file_window = None

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Vertical Layout is going to represent everything
        self.vertical_div = QVBoxLayout(self.centralwidget)

        # Window Representation
        self.upper_horizontal_layout1 = QHBoxLayout()   # AddToVault + ExtractFromVault + ViewMetaData + DeleteFromVault + FindInVault
        self.upper_horizontal_layout2 = QHBoxLayout()   # CurrentPath + Insert

        # Main Buttons -> upper_horizontal_layout1
        # Add To Vault
        self.add_to_vault = CustomButton("Add",QIcon(ICON_1), "Add file(s) into the vault",self.centralwidget)
        self.add_to_vault.set_action(self.open_add_file_window)

        # Extract From Vault
        self.extract_from_vault = CustomButton("Extract",QIcon(ICON_1), "Extract file(s) out of the vault. Files are not deleted.",self.centralwidget)

        # View Metadata
        self.view_metadata = CustomButton("View",QIcon(ICON_1), "View metadata of the currently held item.",self.centralwidget)
        self.view_metadata.set_action(lambda : self.open_view_window(self.tree_widget.currentItem()))

        # Delete from Vault
        self.delete_from_vault = CustomButton("Delete",QIcon(ICON_1), "Delete file(s) in the vault",self.centralwidget)

        # Find in vault
        self.find_in_vault = CustomButton("Find",QIcon(ICON_1), "Find file(s) in the vault",self.centralwidget)
        self.find_in_vault.clicked.connect(self.open_find_dialog)


        # Address bar and Insert Button -> upper_horizontal_layout2
        self.address_bar = CustomLine(text="/", place_holder_text="Path in the vault, e.g, /myFolder/someFolder/", parent=self.centralwidget)
        self.address_bar.returnPressed.connect(lambda : self.on_insert_button_clicked(self.address_bar.text()))

        self.address_bar_button = CustomButton("Insert", QIcon(ICON_1), "Confirm the path to navigate", self.centralwidget)
        self.address_bar_button.set_action(lambda : self.on_insert_button_clicked(self.address_bar.text()))


        # Merging Upper Layouts and adding them into the main layout
        self.upper_horizontal_layout1.addWidget(self.add_to_vault)
        self.upper_horizontal_layout1.addWidget(self.extract_from_vault)
        self.upper_horizontal_layout1.addWidget(self.view_metadata)
        self.upper_horizontal_layout1.addWidget(self.delete_from_vault)
        self.upper_horizontal_layout1.addWidget(self.find_in_vault)
        self.vertical_div.addLayout(self.upper_horizontal_layout1)

        self.upper_horizontal_layout2.addWidget(self.address_bar)
        self.upper_horizontal_layout2.addWidget(self.address_bar_button)
        self.vertical_div.addLayout(self.upper_horizontal_layout2)


        # Tree widget -> vertical_div
        self.tree_widget = CustomTreeWidget(vaultview=True, vaultpath=self.__vault.get_vault_path(),
                                           header_map=self.__vault.get_map(), parent=self.centralwidget)
        self.tree_widget.populate_from_header(self.__vault.get_header()["map"], 0, self.__vault.get_vault_path())
        self.tree_widget.updated_signal.connect(self.address_bar.setText)
        self.vertical_div.addWidget(self.tree_widget)

        # Unknown
        self.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

    # Button insert handle results
    def on_insert_button_clicked(self, path : str, check_location_only : bool = False):
        """If there is path added by the user, then update the tree view with it. Contains an optional boolean value
        which is called in AddFileWindow by import items to determine if the location is ok

        Args:
            path (str): Path inside the vault given by the user

        Returns:
            bool or Tuple[bool,int]: True if managed to find path, False otherwise. Incase of check_location_only, returns path_id as 2nd part of tuple.
        """
        msg_path = f"Could not find the path: '{path}' in the vault, "
        if not path:
            self.show_message("Unknown location", msg_path+"reason: The path is empty")
            return False

        success, list_of_dirs = parse_directory_string(path)
        if not success:
            self.show_message("Unknown location", msg_path+"reason: The path contains invalid characters")
            return False

        success, last_level = self.__vault.determine_if_dir_path_is_valid(list_of_dirs)
        if not success:
            self.show_message("Unknown location", msg_path+f"reason: Provided dir has an invalid path, reached level: {last_level}", "Information")
            return False

        if check_location_only:
            return True, last_level

        if self.tree_widget.populate_from_header(self.__vault.get_map(), last_level, self.__vault.get_vault_path()):
            self.address_bar.setText(path)
            return True
        else:
            self.show_message("Unknown location", msg_path+"reason: Failure to populate from header", "Critical")
            return False

    def show_message(self, window_title : str, message : str, type : str = "Warning"):
        """Display a message box with the given details.

        Args:
            window_title(str): the title of the message
            message(str): the message itself
            type(str) optional: type of the icon to show
        """
        message_box = CustomMessageBox(parent=self)
        if type not in [enum.name for enum in QMessageBox.Icon]:
            message_box.setIcon(QMessageBox.Icon.Warning)
        else:
            message_box.setIcon(QMessageBox.Icon[type])
        message_box.setWindowTitle(window_title)
        message_box.showMessage(message)

    def open_find_dialog(self):
        """On find button click show dialog.
        """
        dialog = FindFileDialog(self)
        dialog.exec()

    def look_for_given_files(self, name : str, extension : str, match_case : bool, is_encrypted : bool):
        """Looks for the given information about the files in the vault.

        Args:
            name (str): Name of the file to look for
            extension (str): The extension of the file
            match_case (bool): If the search should be exact match_case
            is_encrypted (bool): Skip if encrypted
        """
        files = self.__vault.get_files_with(name, extension, match_case, is_encrypted)
        if len(files) == 0:
            self.show_message("Nothing found", f"Any file{' ' if match_case else ' not '}to match case with the name: '{name}{extension}' which its encryption is: '{is_encrypted}' could not be found!")
            return
        # TODO: Optimize
        self.tree_widget.populate_by_request(self.__vault.get_map(), files, self.__vault.get_vault_path())

    def open_view_window(self, held_item : CustomQTreeWidgetItem):
        """On view button click, show view window.
        """
        if held_item is None or held_item.get_saved_obj() is None:
            return None
        if not self.__view_file_window:
            self.__view_file_window = ViewFileWindow(parent=self, item=held_item)
            self.__view_file_window.signal_for_destruction.connect(self.destory_view_file_window)
            self.__view_file_window.show()
        self.clearFocus()

    def add_note_to_vault(self, file_loc : str, extension : str, to_file : int):
        """On add note button click, start addition process

        Args:
            file_loc (str): Location of the note
            extension (str): Extension type
            to_file (int): The file ID to attach into
        """
        file_bytes = None
        with open (file_loc, "rb") as f:
            file_bytes = f.read()
        res = append_bytes_into_file(self.__vault.get_vault_path(), file_bytes)
        if not res[0]:
            # TODO: LOGGER
            print(f"Could not append {file_loc} into the vault because: {res[1]}")
            return
        note_id = self.request_new_id("V")
        the_note = Voice(note_id, to_file, res[2], res[3], extension, get_checksum(file_loc))
        self.insert_item_into_vault(the_note.get_dict(), "V")
        self.request_header_refresh()

    def destory_view_file_window(self, variable : str):
        """Destorys the view file window and cleans up after it
        """
        if self.__view_file_window is not None and variable == "Destroy":
            print("Destroying view file window.")
            self.__view_file_window.list_widget.clear()
            self.__view_file_window.deleteLater()
            self.__view_file_window.destroy(True,True)
            self.__view_file_window = None

    def open_add_file_window(self):
        """On add file button click, show AddFileWindow
        """
        if not self.__add_file_window:
            self.__add_file_window = AddFileWindow(self)
            self.__add_file_window.signal_for_destruction.connect(self.destroy_add_file_window)
            self.__add_file_window.show()
        self.clearFocus()

    def destroy_add_file_window(self, variable : str):
        """Destroys the add file window via emitted signal. This signal is of type str

        Args:
            variable (str): Emitted signal, must be 'Destroy'
        """
        if self.__add_file_window is not None and variable == "Destroy":
            print("Destroying add file window.")
            self.__add_file_window.tree_widget.clear()
            self.__add_file_window.deleteLater()
            self.__add_file_window.destroy(True,True)
            self.__add_file_window = None

    def request_vault_password(self) -> str:
        """Returns the saved password of the vault.

        Returns:
            str: The password of the vault (The one used to access the vault).
        """
        return self.__vault.get_password()

    def request_vault_path(self) -> str:
        """Returns the location of the vault.

        Returns:
            str: The absolute path of the vault.
        """
        return self.__vault.get_vault_path()

    def request_new_id(self , for_what : str) -> int:
        """Requests the vault to get a new ID and adds it into the vault

        Args:
            for_what (str): the letter of the item. (F,D,V)

        Returns:
            int: the new id
        """
        return self.__vault.generate_id(for_what)

    def request_vault_size(self) -> int:
        """Requests the size of the vault

        Returns:
            int: Vault size
        """
        return self.__vault.get_vault_size()

    def request_header_refresh(self): # Called by add_file_window or delete
        """Refreshes the header of the vault, and updates the vault on disk
        """
        self.__vault.refresh_header()
        self.__vault.update_vault_file()

    def request_file_id_addition_into_folder(self, folder_id : int , file_id : int):
        """Adds the given file id into the folder

        Args:
            folder_id (int): folder id
            file_id (int): file id
        """
        self.__vault.insert_file_id_into_folder(folder_id, file_id)

    def insert_item_into_vault(self , ready_dict : dict, type : str):
        """Inserts the given ready_dict into the vault

        Args:
            ready_dict (str): the dict generated by get_file_info
            type (str): the letter of the item. (F,D,V)

        Returns:
            bool: Upon success
        """
        if type == "F":
            self.__vault.insert_file(ready_dict)
        elif type == "V":
            self.__vault.insert_voice_note(ready_dict)
        elif type == "D":
            self.__vault.insert_folder(ready_dict)

    def exit(self) -> None:
        """Cleans up any available threads and tries to close them along with the window.
        """
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.hide()
        self.close()
        # TODO other data
