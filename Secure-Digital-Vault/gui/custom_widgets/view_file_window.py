from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QListWidget, QLabel, QListWidgetItem
from PyQt6.QtGui import QIcon
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from utils.constants import ICON_1

class ViewFileWindow(QMainWindow):
    def __init__(self, item : CustomQTreeWidgetItem = None):
        super().__init__()
        self.setWindowTitle("View File")
        self.setMinimumSize(600, 400)
        self.item = item

        # Central widget and self.vertical_layout
        self.central_widget = QWidget(self)
        self.vertical_layout = QVBoxLayout(self.central_widget)

        # List widget to display items
        self.list_widget = QListWidget(self)
        # TODO destory the window after successful closure.
        for key, value in self.item.get_saved_obj().get_metadata().items():
            element = QListWidgetItem(f"{key}: {value}")
            self.list_widget.addItem(element)

        # Button self.vertical_layout
        button_layout = QHBoxLayout()

        # Add buttons
        encrypt_button = CustomButton("Encrypt", QIcon(ICON_1), "Encrypt file", self.central_widget)
        decrypt_button = CustomButton("Decrypt", QIcon(ICON_1), "Decrypt file", self.central_widget)
        remove_voice_button = CustomButton("Remove VoiceNote", QIcon(ICON_1), "Remove voice note from file", self.central_widget)
        add_voice_button = CustomButton("Add VoiceNote", QIcon(ICON_1), "Add voice note to file", self.central_widget)
        edit_data_button = CustomButton("Edit Data", QIcon(ICON_1), "Edit file data", self.central_widget)

        # Add buttons to self.vertical_layout
        button_layout.addWidget(encrypt_button)
        button_layout.addWidget(decrypt_button)
        button_layout.addWidget(remove_voice_button)
        button_layout.addWidget(add_voice_button)
        button_layout.addWidget(edit_data_button)
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


