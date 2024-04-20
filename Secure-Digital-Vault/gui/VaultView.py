from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QStatusBar, QMessageBox, QDialog
from PyQt6.QtGui import QIcon

from utils.constants import ICON_1
from utils.parsers import parse_directory_string

from classes.vault import Vault
from classes.directory import Directory
from custom_exceptions.classes_exceptions import MissingKeyInJson, JsonWithInvalidData
from logger.logging import Logger

from gui import ViewManager
from gui.custom_widgets.custom_tree_widget import CustomTreeWidget
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_messagebox import CustomMessageBox
from gui.custom_widgets.find_file_dialog import FindFileDialog
from gui.custom_widgets.view_file_window import ViewFileWindow


class VaultViewWindow(QMainWindow):
    # Call The VVW with a constructor that takes an extra parameter which the vault path.
    # Check the vault path
    # Keep the Insert + CurrentPath on top.
    # Keep the detect logic, it will be used for searching for a file.
    # Settings of the vault, to change password, view vault details, get logs, decrypt vault entirely.
    def __init__(self, header : bytes, vault_path : str, VaultViewManager : ViewManager):
        """VaultViewWindow

        Args:
            header (bytes): Extracted Header, Then Decrypted, Then passed as bytes. {Decide if encoding place a role}
        """
        super().__init__()

        # Pointer to ViewManager
        self.__view_manager = VaultViewManager
        # Window Data
        self.__vault = Vault(vault_path)
        try:
            self.__vault.refresh_header(self.__vault.validate_header(header))
        except MissingKeyInJson as e:
            print(e) # TODO
        except JsonWithInvalidData as e:
            print(e) # TODO

        # Window Data
        self.logger = Logger()
        self.threads = []
        self.setObjectName("VaultViewWindow")
        self.setWindowTitle("Vault View Window")
        self.setWindowIcon(QIcon(ICON_1))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.resize(1024, 768)

        # Window References are kept , they go out of scope and are garbage collected, which will destroy the underlying C++ obj.
        self.view_file_window = None

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
        self.tree_widget = CustomTreeWidget(columns=4,vaultview=True, vaultpath=self.__vault.get_vault_path(),
                                           header_map=self.__vault.get_map(), parent=self.centralwidget)
        self.tree_widget.update_columns_with(["Data Created"])
        self.tree_widget.populate_from_header(self.__vault.get_header()["map"], 0, self.__vault.get_vault_path())
        self.tree_widget.updated_signal.connect(self.address_bar.setText)
        self.vertical_div.addWidget(self.tree_widget)

        # Unknown
        self.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

    # Button insert handle results
    def on_insert_button_clicked(self, path : str) -> None:
        """If there is path added by the user, then update the tree view with it

        Args:
            path (str): Path inside the vault given by the user
        """
        if not path:
            return

        success, list_of_dirs = parse_directory_string(path)
        if not success:
            self.show_unknown_location_message(path,"The path contains invalid characters")
            return None

        success, last_level = Directory.determine_if_dir_path_is_valid(list_of_dirs, self.__vault.get_map()["directories"])
        if not success:
            self.show_unknown_location_message(path, f"Provided dir has an invalid path, reached level: {last_level}")
            return None

        if self.tree_widget.populate_from_header(self.__vault.get_map(), last_level, self.__vault.get_vault_path()):
            self.address_bar.setText(path)
        else:
            self.show_unknown_location_message(path,"Failure to populate from header")

    def show_unknown_location_message(self, path: str, reason = None) -> None:
        """Display a message box for an unknown location.

        Args:
            path (str): Unknown location
        """
        message_box = CustomMessageBox(parent=self)
        message_box.setIcon(QMessageBox.Icon.Warning)
        message_box.setWindowTitle("Unknown location")
        message_box.showMessage(f"Could not find the path {path} in the vault, reason: {reason}")

    def open_find_dialog(self):
        """On find button click show dialog.
        """
        dialog = FindFileDialog(self)
        dialog.exec()

    def open_view_window(self, held_item : CustomQTreeWidgetItem):
        """On view button click, show view window.
        """
        if held_item is None or held_item.get_saved_obj() is None:
            return None
        self.view_file_window = ViewFileWindow(held_item)
        self.view_file_window.show()

    # TODO : add delete later for any Windows that can get opened.

    def exit(self) -> None:
        """Cleans up any available threads and tries to close them along with the window.
        """
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.hide()
        self.close()
        self.destroy()
