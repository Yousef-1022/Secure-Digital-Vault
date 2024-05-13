from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QMessageBox
from PyQt6.QtGui import QIcon

from utils.constants import ICON_1, NOTE_LIMIT
from utils.parsers import parse_directory_string
from utils.extractors import get_file_from_vault
from crypto.utils import get_checksum
from file_handle.file_io import append_bytes_into_file, stabilize_after_failed_append

from classes.vault import Vault
from classes.note import Note
from classes.file import File
from classes.directory import Directory
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
from gui.interactions.get_file_window import GetFileWindow
from gui.interactions.delete_file_window import DeleteFileWindow


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
        self.__get_file_window = None
        self.__delete_file_window = None

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Vertical Layout is going to represent everything
        self.vertical_div = QVBoxLayout(self.centralwidget)

        # Window Representation
        self.upper_horizontal_layout1 = QHBoxLayout()   # AddToVault + ExtractFromVault + ViewMetaData + DeleteFromVault + FindInVault
        self.upper_horizontal_layout2 = QHBoxLayout()   # CurrentPath + Insert

        # Main Buttons -> upper_horizontal_layout1
        # Add To Vault
        self.add_to_vault_button = CustomButton("Add",QIcon(ICON_1), "Add file(s) into the vault",self.centralwidget)
        self.add_to_vault_button.set_action(self.open_add_file_window)

        # Extract From Vault
        self.extract_from_vault_button = CustomButton("Extract",QIcon(ICON_1), "Extract file(s) out of the vault. Files are not deleted.",self.centralwidget)
        self.extract_from_vault_button.set_action(self.open_get_file_window)

        # View Metadata
        self.view_metadata_button = CustomButton("View",QIcon(ICON_1), "View metadata of the currently held item.",self.centralwidget)
        self.view_metadata_button.set_action(lambda : self.open_view_window(self.tree_widget.currentItem()))

        # Delete from Vault
        self.delete_from_vault_button = CustomButton("Delete",QIcon(ICON_1), "Delete file(s) in the vault",self.centralwidget)
        self.delete_from_vault_button.set_action(lambda : self.open_delete_window(self.tree_widget.getSelectedItems()))

        # Find in vault
        self.find_in_vault_button = CustomButton("Find",QIcon(ICON_1), "Find file(s) in the vault",self.centralwidget)
        self.find_in_vault_button.clicked.connect(self.open_find_dialog)


        # Address bar and Insert Button -> upper_horizontal_layout2
        self.address_bar = CustomLine(text="/", place_holder_text="Path in the vault, e.g, /myFolder/someFolder/", parent=self.centralwidget)
        self.address_bar.returnPressed.connect(lambda : self.on_insert_button_clicked(self.address_bar.text()))

        self.address_bar_button = CustomButton("Insert", QIcon(ICON_1), "Confirm the path to navigate", self.centralwidget)
        self.address_bar_button.set_action(lambda : self.on_insert_button_clicked(self.address_bar.text()))


        # Merging Upper Layouts and adding them into the main layout
        self.upper_horizontal_layout1.addWidget(self.add_to_vault_button)
        self.upper_horizontal_layout1.addWidget(self.extract_from_vault_button)
        self.upper_horizontal_layout1.addWidget(self.view_metadata_button)
        self.upper_horizontal_layout1.addWidget(self.delete_from_vault_button)
        self.upper_horizontal_layout1.addWidget(self.find_in_vault_button)
        self.vertical_div.addLayout(self.upper_horizontal_layout1)

        self.upper_horizontal_layout2.addWidget(self.address_bar)
        self.upper_horizontal_layout2.addWidget(self.address_bar_button)
        self.vertical_div.addLayout(self.upper_horizontal_layout2)


        # Tree widget -> vertical_div
        self.tree_widget = CustomTreeWidget(parent=self.centralwidget, vaultview=True, vaultpath=self.__vault.get_vault_path(),
                                           header_map=self.__vault.get_map())
        self.tree_widget.populate_from_header(self.__vault.get_map(), 0, self.__vault.get_vault_path())
        self.tree_widget.updated_signal.connect(self.address_bar.setText)
        self.vertical_div.addWidget(self.tree_widget)

        # Additional information labels can be added here
        self.setCentralWidget(self.centralwidget)

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
            self.show_message("Unknown location", msg_path+"reason: The path is empty", parent=self)
            return False

        success, list_of_dirs = parse_directory_string(path)
        if not success:
            self.show_message("Unknown location", msg_path+"reason: The path contains invalid characters", parent=self)
            return False

        success, last_level = self.__vault.determine_if_dir_path_is_valid(list_of_dirs)
        if not success:
            self.show_message("Unknown location", msg_path+f"reason: Provided dir has an invalid path, reached level: {last_level}", "Information", parent=self)
            return False

        if check_location_only:
            return True, last_level

        if self.tree_widget.populate_from_header(self.__vault.get_map(), last_level, self.__vault.get_vault_path()):
            self.address_bar.setText(path)
            return True
        else:
            self.show_message("Unknown location", msg_path+"reason: Failure to populate from header", "Critical", parent=self)
            return False

    def open_view_window(self, held_item : CustomQTreeWidgetItem):
        """On view button click, show view window.
        """
        if held_item is None or held_item.get_saved_obj() is None:
            return None
        if not self.__view_file_window:
            self.__view_file_window = ViewFileWindow(parent=self, item=held_item)
            self.__view_file_window.signal_for_destruction.connect(self.destory_view_file_window)
            self.__view_file_window.show()
        self.delete_from_vault_button.setDisabled(True)
        self.clearFocus()

    def destory_view_file_window(self, variable):
        """Destorys the view file window and cleans up after it
        """
        if self.__view_file_window is not None:
            command = variable
            if isinstance(variable, list):
                print("ViewFileWindow updates header.")
                command = variable[0]
                self.update_file_data_in_vault(variable[1])

            if command == "Destroy":
                print("Destroying view file window without updating header.")
                self.__view_file_window.list_widget.clear()
                self.__view_file_window.deleteLater()
                self.__view_file_window.destroy(True,True)
                self.__view_file_window = None
        self.delete_from_vault_button.setEnabled(True)

    def open_add_file_window(self):
        """On add file button click, show AddFileWindow
        """
        if not self.__add_file_window:
            self.__add_file_window = AddFileWindow(self)
            self.__add_file_window.signal_for_destruction.connect(self.destroy_add_file_window)
            self.__add_file_window.show()
        self.delete_from_vault_button.setDisabled(True)
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
        self.delete_from_vault_button.setEnabled(True)

    def open_get_file_window(self):
        """On get file button click, show GetFileWindow
        """
        if not self.__get_file_window:
            self.__get_file_window = GetFileWindow(self, self.tree_widget.getSelectedItems())
            self.__get_file_window.signal_for_destruction.connect(self.destroy_get_file_window)
            self.__get_file_window.show()
        self.delete_from_vault_button.setDisabled(True)
        self.clearFocus()

    def destroy_get_file_window(self, variable : str):
        """Destroys the get file window via emitted signal. This signal is of type str

        Args:
            variable (str): Emitted signal, must be 'Destroy'
        """
        if self.__get_file_window is not None and variable == "Destroy":
            print("Destroying get file window.")
            self.__get_file_window.list_widget.clear()
            self.__get_file_window.deleteLater()
            self.__get_file_window.destroy(True,True)
            self.__get_file_window = None
        self.delete_from_vault_button.setEnabled(True)

    def open_delete_window(self, held_items : list[CustomQTreeWidgetItem]):
        """On delete button click, show delete window
        """
        if not held_items or len(held_items) < 1:
            return None
        if not self.__delete_file_window:
            self.__delete_file_window = DeleteFileWindow(parent=self, items=held_items)
            self.__delete_file_window.signal_for_destruction.connect(self.destory_delete_file_window)
            self.__delete_file_window.show()
        self.add_to_vault_button.setDisabled(True)
        self.clearFocus()

    def destory_delete_file_window(self, variable):
        """Destorys the delete file window and cleans up after it
        """
        if self.__delete_file_window is not None and variable == "Destroy":
            print("Destroying add file window.")
            self.__delete_file_window.list_widget.clear()
            self.__delete_file_window.deleteLater()
            self.__delete_file_window.destroy(True,True)
            self.__delete_file_window = None
        self.add_to_vault_button.setEnabled(True)

    def show_message(self, window_title : str, message : str, type : str = "Warning", parent : QWidget = None):
        """Display a message box with the given details.

        Args:
            window_title(str): the title of the message
            message(str): the message itself
            type(str) optional: type of the icon to show
            parent(QWidget) optional: parent to assign the message box to
        """
        if parent:
            message_box = CustomMessageBox(parent=parent)
        else:
            message_box = CustomMessageBox(parent=self)
        if type not in [enum.name for enum in QMessageBox.Icon]:
            message_box.setIcon(QMessageBox.Icon.Warning)
        else:
            message_box.setIcon(QMessageBox.Icon[type])
        message_box.setWindowTitle(window_title)
        message_box.showMessage(message)
        message_box.close()
        message_box.deleteLater()

    def open_find_dialog(self):
        """On find button click show dialog.
        """
        dialog = FindFileDialog(self)
        dialog.exec()

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

    def request_header_refresh(self, refresh_tree : bool = False): # Called by add_file_window or delete
        """Refreshes the header of the vault, and updates the vault on disk

        Args:
            refresh_tree (bool, optional): Boolean to indicate whether to refresh the tree. Defaults to False.
        """
        # TODO: Thread
        self.__vault.refresh_header()
        if refresh_tree:
            self.tree_widget.populate_from_header(self.__vault.get_map(), self.tree_widget.current_path, self.__vault.get_vault_path())
        self.__vault.update_vault_file()

    def request_file_id_addition_into_folder(self, folder_id : int , file_id : int):
        """Adds the given file id into the folder

        Args:
            folder_id (int): folder id
            file_id (int): file id
        """
        self.__vault.insert_file_id_into_folder(folder_id, file_id)

    def request_given_files(self, name : str, extension : str, match_case : bool, is_encrypted : bool, has_note : bool):
        """Looks for the given information about the files in the vault.

        Args:
            name (str): Name of the file to look for
            extension (str): The extension of the file which is checked before hand
            match_case (bool): If the search should be exact match_case
            is_encrypted (bool): Skip if encrypted
            has_note (bool): Skip if False
        """
        files = self.__vault.get_files_with(name, extension, match_case, is_encrypted, has_note)
        if len(files) == 0:
            self.show_message("Nothing found", f"Any file{' ' if match_case else ' not '}to match case with the name: '{name}{extension}' which its encryption is: '{is_encrypted}' and note existence is: '{has_note}' could not be found!", parent=self)
            return
        self.tree_widget.populate_by_request(self.__vault.get_map(), files, self.__vault.get_vault_path())

    def request_files_from_vault(self, folder_id : int, get_path_as_int : bool, parent_name : str = None) -> list[File]:
        """Gets all the Files from the Vault which exist within the specified directory and its subfolders.

        Args:
            lst (int): Folder id
            get_path_as_int (bool): Whether to keep the File path as default, or Path id
            parent_name (str): Name of the parent folder

        Returns:
            dict: List of File
        """
        return self.__vault.get_files_belonging_in_id(folder_id, get_path_as_int, parent_name)

    def request_data_shift(self, amount_to_shift : int, direction : bool, at_index : int):
        """Shifts all the byte indexes in the map after delete according to the given parameters

        Args:
            amount_to_shift (int): The amount to shift
            data_index_shifter (int): Target files and notes at this index
        """
        self.__vault.data_index_shifter(amount_to_shift, direction, at_index)

    def request_files_and_folders_from_vault(self, belong_to: int) -> list:
        """Gets a list of Files and Directories which belong to the given id

        Args:
            belong_to (int): The id that owns the files and folders.

        Returns:
            list: List of Files and Directories
        """
        return self.__vault.get_items_under_id(belong_to)

    def request_path_string(self, the_id : int, full_path : bool = True, type : str = "D") -> str:
        """Gets either the full path of the given folder id from the vault, or only the path from the given id

        Args:
            the_id (int): The folder id to get its full path.
            full_path (bool): Whether to get the fullpath /path/to/ , or to get the path starting from the the_id the_id/path/to/

        Returns:
            str: Full path, e.g /path/to/ or path/to
        """
        if full_path:
            return self.__vault.get_full_path(the_id)
        else:
            res = self.__vault.get_name_of_id(the_id, type)
            if res == '':
                return '/'
            return f'{res}/'

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
            self.__vault.insert_note(ready_dict)
        elif type == "D":
            self.__vault.insert_folder(ready_dict)

    def update_folder_in_vault(self, folder : Directory):
        """Updates the folder data in the vault

        Args:
            folder (Directory): The folder to update with, this folder must be valid.

        Returns:
            bool: Upon success
        """
        self.__vault.update_folder_in_vault(folder)

    def update_vault_file_size(self, new_size : int):
        """Updates the vault's file_size key with the new size, this is requested after deletion

        Args:
            new_size (int): The new size of files in the vault.
        """
        self.__vault.update_file_size_of_vault(new_size)

    def add_note_to_vault(self, file_loc : str, extension : str, to_file : int):
        """On add note button click, start addition process

        Args:
            file_loc (str): Location of the note
            extension (str): Extension type
            to_file (int): The file ID to attach into
        """
        self.add_to_vault_button.setDisabled(True)
        self.delete_from_vault_button.setDisabled(True)
        file_bytes = None
        with open (file_loc, "rb") as f:
            file_bytes = f.read()
        res = append_bytes_into_file(self.__vault.get_vault_path(), file_bytes)
        if not res[0]:
            error_str = stabilize_after_failed_append(self.__vault.get_vault_path(), res[1], res[2], res[3]-res[2])
            error_str += f", could not append note {file_loc} into the vault."
            self.logger.error(error_str)
            self.show_message("Error", "Couldn't add a note note. Check logs.", "Error" , parent=self)
            return
        note_id = self.request_new_id("V")
        note_info = {
            "id" : note_id,
            "owned_by_file" : to_file,
            "loc_start" : res[2],
            "loc_end" : res[3],
            "type" : extension,
            "checksum" : get_checksum(file_loc)
        }
        the_note = Note(note_info)
        self.insert_item_into_vault(the_note.get_as_dict(), "V")
        self.request_header_refresh(refresh_tree=False)
        self.add_to_vault_button.setEnabled(True)
        self.delete_from_vault_button.setEnabled(True)

    def get_note_from_vault(self, file_loc : str, note_id : int):
        """Gets the given note from the vault

        Args:
            file_loc (str): Location of the note
            note_id (int): The note ID to get
        """
        note_dict = self.__vault.get_id_from_vault(note_id, "V")
        if not note_dict[0]: # Note not existing
            msg = f"Couldn't get note due to: {note_dict[1]}"
            self.logger.error(msg)
            self.show_message("Error", msg, "Error", self)
            return
        file_dict = self.__vault.get_id_from_vault(note_dict[1]["owned_by_file"], "F")
        if not file_dict[0]:  # Note not belonging to file
            msg = f"Couldn't get note due to: {file_dict[1]}"
            self.logger.error(msg)
            self.show_message("Error", msg, "Error", self)
            return
        note_name = f'{file_dict[1]["metadata"]["name"]}_note.{note_dict[1]["type"]}'
        file_bytes = get_file_from_vault(self.__vault.get_vault_path(), note_dict[1]["loc_start"], note_dict[1]["loc_end"], NOTE_LIMIT)
        res = append_bytes_into_file(file_loc, file_bytes, create_file=True, file_name=note_name)
        msg = f'{file_loc}{note_name}'
        msg_title = "Success"
        if not res[0]:
            msg = f"Couldn't create {msg} note due to: {res[1]}"
            msg_title = "Failure"
            self.logger.error(msg)
        self.show_message(msg_title, msg, "Information", self)
        return

    def get_item_class_from_vault(self, item_id : int, type : str) -> object:
        """Gets the item with the given id and type from the vault

        Args:
            item_id (int): The id of the item
            type (str): The letter of the item (F,D,V)

        Returns:
            object: The item itself
        """
        res = self.__vault.get_id_from_vault(item_id, type, False)
        if not res[0]:
            self.logger.error(res[1])
            return None
        return res[1]

    def update_file_data_in_vault(self, file : File):
        """On view file exit, update the header incase it was modified

        Args:
            file (File): The file itself
        """
        if not file:
            return
        file.validate_mapped_data(file.get_as_dict())
        self.__vault.update_file_in_vault(file)
        self.request_header_refresh(refresh_tree=False)

    def remove_folder_without_files(self, folder_id : int):
        """Removes the folder from the vault, it shall not contain any files.

        Args:
            folder_id (int): Removal of folder_id from the vault
        """
        res = self.__vault.safe_remove_folder(folder_id)
        if res[0]:
            if res[1] != "":
                self.logger.warn(res[1])
            return
        else:
            self.logger.error(res[1])

    def remove_file_from_vault(self, file_id : int):
        """Removes the file from the vault

        Args:
            file_id (int): The file_id to remove
        """
        self.__vault.remove_file(file_id)

    def remove_note_from_vault(self, note_id : int):
        """Removes the note from the vault

        Args:
            note_id (int): The folder_id to remove
        """
        self.__vault.remove_note(note_id)

    def closeEvent(self, event):
        """Override for close window for safe shutdown.
        """
        print(f'({self.logger.get_all_logs()})')
        #TODO: More logic
        super().closeEvent(event)

    def exit(self) -> None:
        """Cleans up any available threads and tries to close them along with the window.
        """
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.hide()
        self.close()
        # TODO other data
