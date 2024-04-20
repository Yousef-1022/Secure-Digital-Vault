from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QStatusBar, QFrame, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal

from gui.VaultSearch import VaultSearchWindow
from gui.VaultView import VaultViewWindow
from gui.VaultCreate import VaultCreateWindow
from gui.custom_widgets.custom_button import CustomButton

from logger.logging import Logger

from utils.constants import ICON_1


class WindowManager(QMainWindow):

    signal_to_open_window = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # Special Data
        self.__data = None
        self.__vault_pointer = ""
        self.signal_to_open_window.connect(self.handle_window)
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

    def set_special(self , data : bytes):
        self.__data = data

    def set_vault_pointer(self, file_path : str):
        self.__vault_pointer = file_path

    def handle_window(self, signal : str):
        if signal == "VaultSearch":
            self.__VaultCreateView_exit()
            self.__VaultView_exit()
            self.__show_VaultSearch()
        elif signal == "VaultCreate":
            self.__VaultSearchView_exit()
            self.__VaultView_exit()
            self.__show_VaultCreate()
        elif signal == "VaultView":
            self.__VaultCreateView_exit()
            self.__VaultSearchView_exit()
            self.__show_VaultView()
        else:
            self.__VaultSearchView_exit()
            self.__VaultCreateView_exit()
            self.__VaultView_exit()
            self.show()
        return

    def __show_VaultSearch(self):
        if not self.__VaultSearchView:
            self.__VaultSearchView = VaultSearchWindow(self)
        self.__VaultSearchView.show()
        self.close()

    def __VaultSearchView_exit(self):
        if self.__VaultSearchView:
            self.__VaultSearchView.exit()
            self.__VaultSearchView = None

    def __show_VaultCreate(self):
        if not self.__VaultCreateView:
            self.__VaultCreateView = VaultCreateWindow(self)
        self.__VaultCreateView.show()
        self.close()

    def __VaultCreateView_exit(self):
        if self.__VaultCreateView:
            self.__VaultCreateView.exit()
            self.__VaultCreateView = None

    def __show_VaultView(self):
        if not self.__VaultView:
            self.__VaultView = VaultViewWindow(self.__data,self.__vault_pointer,self)
        self.__VaultView.show()
        self.close()

    def __VaultView_exit(self):
        if self.__VaultView:
            self.__VaultView.exit()
            self.__VaultView = None

