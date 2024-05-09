from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QListWidget, QLabel, QListWidgetItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal

from classes.file import File
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui import VaultView

from utils.constants import ICON_1
from utils.parsers import parse_timestamp_to_string


class ViewFileWindow(QMainWindow):

    signal_for_destruction = pyqtSignal(str)

    def __init__(self, parent : VaultView, item : CustomQTreeWidgetItem):
        super().__init__(parent)
        self.setWindowTitle("View File")
        self.setMinimumSize(600, 400)
        self.item = item
        self.__vc = False
        self.__encrypted = False

        # Central widget and self.vertical_layout
        self.central_widget = QWidget(self)
        self.vertical_layout = QVBoxLayout(self.central_widget)

        # List widget to display items
        self.list_widget = QListWidget(self)
        if self.item.get_in_vault_location():
            self.list_widget.addItem(QListWidgetItem(f"Location: {self.item.get_in_vault_location()}"))
        for key, value in self.item.get_saved_obj().get_metadata().items():
            if key == "last_modified" or key == "data_created":
                element = QListWidgetItem(f"{key}: {parse_timestamp_to_string(value)}")
            elif key == "icon_data_start" or key == "icon_data_end":
                continue
            else:
                if key == "voice_note_id" and value != -1:
                    self.__vc = True
                element = QListWidgetItem(f"{key}: {value}")
            self.list_widget.addItem(element)
        if isinstance(self.item.get_saved_obj(), File):
            self.__encrypted = self.item.get_saved_obj().get_file_encrypted()
            self.list_widget.addItem(QListWidgetItem(f"file_encrypted: {self.__encrypted}"))

        # Button self.vertical_layout
        button_layout = QHBoxLayout()

        # Add buttons
        encrypt_button = CustomButton("Encrypt", QIcon(ICON_1), "Encrypt file", self.central_widget)
        decrypt_button = CustomButton("Decrypt", QIcon(ICON_1), "Decrypt file", self.central_widget)
        remove_voice_button = CustomButton("Remove VoiceNote", QIcon(ICON_1), "Remove voice note from file", self.central_widget)
        add_voice_button = CustomButton("Add VoiceNote", QIcon(ICON_1), "Add voice note to file", self.central_widget)
        get_voice_button = CustomButton("Get VoiceNote", QIcon(ICON_1), "Get the VoiceNote", self.central_widget)
        if not self.__vc:
            get_voice_button.setDisabled(True)

        # Add buttons to self.vertical_layout
        button_layout.addWidget(encrypt_button)
        button_layout.addWidget(decrypt_button)
        button_layout.addWidget(remove_voice_button)
        button_layout.addWidget(add_voice_button)
        button_layout.addWidget(get_voice_button)
        self.vertical_layout.addLayout(button_layout)
        self.vertical_layout.addWidget(self.list_widget)

        # Panel self.vertical_layout for bottom left
        panel_layout = QHBoxLayout()
        self.vertical_layout.addLayout(panel_layout)

        # Lock icon
        lock_icon = QIcon(ICON_1)
        lock_label = QLabel(self)
        lock_label.setPixmap(lock_icon.pixmap(20))  # Adjust size as needed
        panel_layout.addWidget(lock_label)

        # Additional information labels can be added here
        self.setCentralWidget(self.central_widget)

    def closeEvent(self, event):
        """Override for close window and clean up any remaining items
        """
        self.signal_for_destruction.emit("Destroy")
        super().closeEvent(event)

    def add_voice_note(self):
        pass
        # Logic: Open a dialog, and vc location. (CAN BE ANYTHING)