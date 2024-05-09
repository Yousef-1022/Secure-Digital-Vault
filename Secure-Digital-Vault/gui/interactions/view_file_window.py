from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QListWidget, QLabel, QListWidgetItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal

from classes.file import File
from classes.directory import Directory

from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui.interactions.add_voice_dialog import AddVoiceDialog
from gui import VaultView

from utils.constants import ICON_1
from utils.parsers import parse_timestamp_to_string


class ViewFileWindow(QMainWindow):

    signal_for_destruction = pyqtSignal(str)

    def __init__(self, parent : VaultView, item : CustomQTreeWidgetItem):
        super().__init__(parent)
        self.setWindowTitle("View Item")
        self.setMinimumSize(600, 400)
        self.item = item
        self.__encrypted = False

        # Central widget and self.vertical_layout
        self.central_widget = QWidget(self)
        self.vertical_layout = QVBoxLayout(self.central_widget)

        # Add buttons
        self.button_layout = QHBoxLayout()
        self.encrypt_button = CustomButton("Encrypt", QIcon(ICON_1), "Encrypt file", self.central_widget)
        self.decrypt_button = CustomButton("Decrypt", QIcon(ICON_1), "Decrypt file", self.central_widget)
        self.remove_voice_button = CustomButton("Remove VoiceNote", QIcon(ICON_1), "Remove voice note from file", self.central_widget)
        self.add_voice_button = CustomButton("Add VoiceNote", QIcon(ICON_1), "Add voice note to file", self.central_widget)
        self.add_voice_button.set_action(self.add_voice_note)
        self.get_voice_button = CustomButton("Get VoiceNote", QIcon(ICON_1), "Get the VoiceNote", self.central_widget)
        self.get_voice_button.set_action(self.get_voice_note)

        # List widget to display items
        self.list_widget = QListWidget(self)
        self.__fullfill_list()

        # Add buttons to self.vertical_layout
        self.button_layout.addWidget(self.encrypt_button)
        self.button_layout.addWidget(self.decrypt_button)
        self.button_layout.addWidget(self.remove_voice_button)
        self.button_layout.addWidget(self.add_voice_button)
        self.button_layout.addWidget(self.get_voice_button)
        self.vertical_layout.addLayout(self.button_layout)
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

    def __update_buttons(self):
        """Updates the buttons according to the data of the item
        """
        if isinstance(self.item.get_saved_obj(), File):
            if self.item.get_saved_obj().get_file_encrypted():
                self.encrypt_button.setDisabled(True)
                self.decrypt_button.setEnabled(True)
            else:
                self.encrypt_button.setEnabled(True)
                self.decrypt_button.setDisabled(True)
            if self.item.get_saved_obj().get_metadata()["voice_note_id"] != -1:
                self.remove_voice_button.setEnabled(True)
                self.add_voice_button.setDisabled(True)
                self.get_voice_button.setEnabled(True)
            else:
                self.remove_voice_button.setDisabled(True)
                self.add_voice_button.setEnabled(True)
                self.get_voice_button.setDisabled(True)
        elif isinstance(self.item.get_saved_obj(), Directory):
            self.encrypt_button.setDisabled(True)
            self.decrypt_button.setDisabled(True)
            self.remove_voice_button.setDisabled(True)
            self.add_voice_button.setDisabled(True)
            self.get_voice_button.setDisabled(True)

    def __fullfill_list(self):
        """Fullfills the list of the view file window, and updates the buttons accordingly
        """
        self.list_widget.clear()
        if self.item.get_in_vault_location():
            self.list_widget.addItem(QListWidgetItem(f"Location: {self.item.get_in_vault_location()}"))
        for key, value in self.item.get_saved_obj().get_metadata().items():
            if key == "last_modified" or key == "data_created":
                element = QListWidgetItem(f"{key}: {parse_timestamp_to_string(value)}")
            elif key == "icon_data_start" or key == "icon_data_end":
                continue
            else:
                element = QListWidgetItem(f"{key}: {value}")
            self.list_widget.addItem(element)
        if isinstance(self.item.get_saved_obj(), File):
            self.__encrypted = self.item.get_saved_obj().get_file_encrypted()
            self.list_widget.addItem(QListWidgetItem(f"file_encrypted: {self.__encrypted}"))
        self.__update_buttons()

    def closeEvent(self, event):
        """Override for close window and clean up any remaining items
        """
        print("ViewFileWindow: Signaled for destruction")
        self.signal_for_destruction.emit("Destroy")
        super().closeEvent(event)

    def add_voice_note(self):
        """Adds a note to the file.
        """
        avd = AddVoiceDialog(self.item.get_saved_obj().get_id(),parent=self.parent())
        avd.exec()
        avd.close()
        avd.deleteLater()
        avd.destroy(True,True)
        avd = None
        self.__fullfill_list()

    def get_voice_note(self):
        """Gets the voice note of the file
        """
        pass