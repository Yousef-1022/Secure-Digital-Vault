from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QFrame, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal

from gui.VaultSearch import VaultSearchWindow
from gui.VaultView import VaultViewWindow
from gui.VaultCreate import VaultCreateWindow
from gui.custom_widgets.custom_button import CustomButton

from utils.constants import ICON_6, MINIMUM_WINDOW_HEIGHT, MINIMUM_WINDOW_WIDTH


class ViewManager(QMainWindow):
    """Used to manage the initial point of the Vault"""

    signal_to_open_window = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # Special Data
        self.__data_h = None
        self.__data_f = None
        self.__data_s = 0
        self.__data_p = None
        self.__vault_pointer = ""
        self.signal_to_open_window.connect(self.handle_window)
        # Manager Data
        self.threads = []
        self.__VaultCreateView = None
        self.__VaultSearchView = None
        self.__VaultView = None

        # QtData
        self.setObjectName("Vault Manager")
        self.setWindowTitle("Vault Manager")
        self.setWindowIcon(QIcon(ICON_6))
        self.setMinimumWidth(MINIMUM_WINDOW_WIDTH)
        self.setMaximumWidth(MINIMUM_WINDOW_WIDTH)
        self.setMinimumHeight(MINIMUM_WINDOW_HEIGHT)
        self.setMaximumHeight(MINIMUM_WINDOW_HEIGHT)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Main Layout
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins from main layout


        # Welcome Frame
        self.welcome_frame = QFrame(self.centralwidget)
        self.welcome_frame.setObjectName("welcomeFrame")
        self.welcome_layout = QVBoxLayout(self.welcome_frame)
        self.welcome_layout.setContentsMargins(0, 55, 0, 0)
        self.welcome_label = QLabel("Welcome to the Secure Digital Vault", self.welcome_frame)
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.welcome_layout.addWidget(self.welcome_label)

        # Search and Create buttons
        self.search_vault = CustomButton("Find Vault", QIcon(), "Search for a Vault on your system", self.centralwidget)
        self.search_vault.set_action(self.__show_VaultSearch)
        self.search_vault.customContextMenuRequested.disconnect()
        self.create_vault = CustomButton("Create Vault", QIcon(), "Create a Vault", self.centralwidget)
        self.create_vault.set_action(self.__show_VaultCreate)
        self.create_vault.customContextMenuRequested.disconnect()

        # Buttons frame
        self.buttons_frame = QFrame(self.centralwidget)
        self.buttons_frame.setObjectName("buttonsFrame")
        self.buttons_layout = QHBoxLayout(self.buttons_frame)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.addWidget(self.search_vault)
        self.buttons_layout.addWidget(self.create_vault)

        # Add into main layout
        self.main_layout.addWidget(self.welcome_frame, alignment=Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.buttons_frame)

        # Additional information labels can be added here
        self.setCentralWidget(self.centralwidget)

        # CSS
        self.setStyleSheet("""
            ViewManager {
                background-image: url(:/assets/background.png);
                background-repeat: no-repeat;
                background-position: top;
                background-attachment: fixed;
                background-color: white;
            }
        """)
        self.welcome_label.setStyleSheet("""
            font-family: Times New Roman;
            font-weight: bold;
            font-size: 15px;
            color: black;
        """)

        self.search_vault.setStyleSheet("""
            background-image: url(:/assets/icon18.png);
            background-repeat: no-repeat;
            background-color: transparent;
            border: none;
            text-align: bottom;
            vertical-align: bottom;
            font-family: Times New Roman;
            font-weight: bold;
            font-size: 15px;
            min-width: 150px;
            min-height: 150px;
            padding-top: 10px;
        """)

        self.create_vault.setStyleSheet("""
            background-image: url(:/assets/icon19.png);
            background-repeat: no-repeat;
            background-color: transparent;
            border: none;
            text-align: bottom;
            vertical-align: bottom;
            font-family: Times New Roman;
            font-weight: bold;
            font-size: 15px;
            min-width: 150px;
            min-height: 150px;
            padding-top: 10px;
        """)

    def set_special_h(self , data : bytes):
        self.__data_h = data

    def set_special_f(self , data : bytes):
        self.__data_f = data

    def set_special_s(self, data : int):
        self.__data_s = data

    def set_special_p(self , data : bytes):
        self.__data_p = data

    def set_vault_pointer(self, file_path : str):
        self.__vault_pointer = file_path

    def handle_window(self, signal : str):
        if signal == "VaultSearch":
            self.__VaultCreateView_exit()
            self.__show_VaultSearch()
        elif signal == "VaultCreate":
            self.__VaultSearchView_exit()
            self.__show_VaultCreate()
        elif signal == "VaultView":
            self.__VaultCreateView_exit()
            self.__VaultSearchView_exit()
            self.__show_VaultView()
        else:
            self.__VaultSearchView_exit()
            self.__VaultCreateView_exit()
            self.show()
        return

    def __show_VaultSearch(self):
        if not self.__VaultSearchView:
            self.__VaultSearchView = VaultSearchWindow(self)
        self.setParent(self.__VaultSearchView)
        self.hide()
        self.__VaultSearchView.show()

    def __VaultSearchView_exit(self):
        if self.__VaultSearchView:
            self.__VaultSearchView.tree_widget.clear()
            self.__VaultSearchView.exit()
            self.__VaultSearchView.deleteLater()
            self.__VaultSearchView = None
        self.setParent(None)

    def __show_VaultCreate(self):
        if not self.__VaultCreateView:
            self.__VaultCreateView = VaultCreateWindow(self)
        self.setParent(self.__VaultCreateView)
        self.hide()
        self.__VaultCreateView.show()

    def __VaultCreateView_exit(self):
        if self.__VaultCreateView:
            self.__VaultCreateView.item_list_widget.clear()
            self.__VaultCreateView.exit()
            self.__VaultCreateView.deleteLater()
            self.__VaultCreateView = None
        self.setParent(None)

    def __show_VaultView(self):
        if not self.__VaultView:
            self.__VaultView = VaultViewWindow(self.__data_h, self.__data_f, self.__data_s, self.__data_p, self.__vault_pointer)

        # Corruption Handle
        if len(self.__VaultView.threads) != 0 and self.__VaultView.threads[0] == -1:
            self.hide()
            self.close_self()
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()
            return

        self.setParent(self.__VaultView)
        self.__VaultView.show()
        self.hide()
        self.close_self()

    def close_self(self):
        self.__VaultCreateView_exit()
        self.__VaultSearchView_exit()
        self.__data_h = None
        self.__data_f = None
        self.__data_p = None
        self.__vault_pointer = ""
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.close()
        self.deleteLater()
