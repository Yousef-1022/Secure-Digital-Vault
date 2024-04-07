from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QStatusBar
from PyQt6.QtGui import QIcon

from utils.constants import ICON_1

from classes.vault import Vault
from custom_exceptions.classes_exceptions import MissingKeyInJson, JsonWithInvalidData
from logger.logging import Logger

from gui.custom_widgets.custom_tree_widget import CustomTreeWidget
from gui.custom_widgets.custom_button import CustomButton


class VaultViewWindow(QMainWindow):
    # Call The VVW with a constructor that takes an extra parameter which the vault path.
    # Check the vault path
    # Keep the Insert + CurrentPath on top.
    # Keep the detect logic, it will be used for searching for a file.
    # Settings of the vault, to change password, view vault details, get logs, decrypt vault entirely.
    def __init__(self, header : bytes, vault_path : str):
        """VaultViewWindow

        Args:
            header (bytes): Extracted Header, Then Decrypted, Then passed as bytes. {Decide if encoding place a role}
        """
        super().__init__()

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

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Vertical Layout is going to represent everything
        self.vertical_div = QVBoxLayout(self.centralwidget)

        # Window Representation
        self.upper_horizontal_layout = QHBoxLayout()    # AddToVault + ExtractFromVault + ViewMetaData + DeleteFromVault + FindInVault

        # Buttons
        self.add_to_vault = CustomButton("Add",QIcon(ICON_1), "Add file(s) into the vault",self.centralwidget)
        self.extract_from_vault = CustomButton("Extract",QIcon(ICON_1), "Extract file(s) out of the vault. Files are not deleted.",self.centralwidget)
        self.view_metadata = CustomButton("View",QIcon(ICON_1), "View metadata of the currently held item.",self.centralwidget)
        self.delete_from_vault = CustomButton("Delete",QIcon(ICON_1), "Delete file(s) in the vault",self.centralwidget)
        self.find_in_vault = CustomButton("Find",QIcon(ICON_1), "Find file(s) in the vault",self.centralwidget)

        # Merging buttons and adding them into the main layout
        self.upper_horizontal_layout.addWidget(self.add_to_vault)
        self.upper_horizontal_layout.addWidget(self.extract_from_vault)
        self.upper_horizontal_layout.addWidget(self.view_metadata)
        self.upper_horizontal_layout.addWidget(self.delete_from_vault)
        self.upper_horizontal_layout.addWidget(self.find_in_vault)
        self.vertical_div.addLayout(self.upper_horizontal_layout)

        # Tree widget -> vertical_div
        self.tree_widget = CustomTreeWidget(columns=4,vaultview=True, vaultpath=self.__vault.get_vault_path(),
                                           header_map=self.__vault.get_map(), parent=self.centralwidget)
        self.tree_widget.update_columns_with(["Data Created"])
        self.tree_widget.populate_from_header(self.__vault.get_header()["map"],"/",self.__vault.get_vault_path())
        self.vertical_div.addWidget(self.tree_widget)

        # Unknown
        self.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)