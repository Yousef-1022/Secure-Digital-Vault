from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QStatusBar
from PyQt6.QtGui import QIcon

from utils.constants import ICON_5

from classes.vault import Vault
from logger.logging import Logger
from custom_exceptions.classes_exceptions import MissingKeyInJson, JsonWithInvalidData

from gui.custom_widgets.custom_tree_widget import CustomTreeWidget


class VaultViewWindow(QMainWindow):
    # Call The VVW with a constructor that takes an extra parameter which the vault path.
    # Check the vault path
    # Use QTreeViewModel (the custom one you have is useful)
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
        self.setWindowIcon(QIcon(ICON_5))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.resize(1024, 768)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Vertical Layout is going to represent everything
        self.vertical_div = QVBoxLayout(self.centralwidget)

        # Tree widget -> vertical_div
        self.treeWidget = CustomTreeWidget(columns=4,vaultview=True, vaultpath=self.__vault.get_vault_path(),
                                           header_map=self.__vault.get_map(), parent=self.centralwidget)
        self.treeWidget.update_columns_with(["Data Created"])
        self.treeWidget.populate_from_header(self.__vault.get_header()["map"],"/",self.__vault.get_vault_path())
        self.vertical_div.addWidget(self.treeWidget)

        # Unknown
        self.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)