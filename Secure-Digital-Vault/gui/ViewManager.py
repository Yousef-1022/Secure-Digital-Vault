from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QStatusBar, QFrame, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from gui.VaultSearch import VaultSearchWindow
from gui.VaultView import VaultViewWindow
from gui.VaultCreate import VaultCreateWindow
from gui.custom_widgets.custom_button import CustomButton

from logger.logging import Logger

from utils.constants import ICON_1


class WindowManager(QMainWindow):
    def __init__(self):
        super().__init__()

        # Manager Data
        self.logger = Logger()
        self.threads = []
        self.__VaultCreateView = None
        self.__VaultSearchView = None
        self.__VaultView = None


        # QtData
        self.setObjectName("Vault Manager")
        self.setWindowTitle("Vault Manager")
        self.setWindowIcon(QIcon(ICON_1))
        self.setMinimumWidth(640)
        self.setMinimumHeight(480)
        self.resize(640, 480)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Main Layout
        self.main_layout = QVBoxLayout(self.centralwidget)

        # Welcome Frame
        self.welcome_frame = QFrame(self.centralwidget)
        self.welcome_frame.setObjectName("welcomeFrame")
        self.welcome_layout = QVBoxLayout(self.welcome_frame)
        self.welcome_label = QLabel("Welcome to Vault Manager", self.welcome_frame)
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_layout.addWidget(self.welcome_label)
        
        # Search and Create buttons
        self.search_vault = CustomButton("Find Vault", QIcon(ICON_1), "Search for a Vault on your system", self.centralwidget)
        self.search_vault.set_action(self.__show_VaultSearch)
        self.create_vault = CustomButton("Create Vault", QIcon(ICON_1), "Create a Vault", self.centralwidget)
        self.create_vault.set_action(self.__show_VaultCreate)
        
        # Buttons frame
        self.buttons_frame = QFrame(self.centralwidget)
        self.buttons_frame.setObjectName("buttonsFrame")
        self.buttons_layout = QHBoxLayout(self.buttons_frame)
        self.buttons_layout.addWidget(self.search_vault)
        self.buttons_layout.addWidget(self.create_vault)

        # Add into main div
        self.main_layout.addWidget(self.welcome_frame)
        self.main_layout.addWidget(self.buttons_frame)

        self.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

    def __show_VaultSearch(self):
        if not self.__VaultSearchView:
            self.__VaultSearchView = VaultSearchWindow()
        self.__VaultSearchView.show()
        self.close()

    def __show_VaultCreate(self):
        if not self.__VaultCreateView:
            self.__VaultCreateView = VaultCreateWindow()
        self.__VaultCreateView.show()
        self.close()

