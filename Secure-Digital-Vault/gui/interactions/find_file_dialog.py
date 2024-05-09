from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QLabel, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line import CustomLine
from gui import VaultView

from utils.constants import ICON_1
from utils.helpers import is_proper_extension


class FindFileDialog(QDialog):

    finished_signal = pyqtSignal(dict)

    def __init__(self, parent: VaultView):
        super().__init__(parent)
        self.setWindowTitle("Find Files")

        self.vertical_layout = QVBoxLayout(self)
        self.horizontal_layout = QHBoxLayout()

        # String name in file
        self.find_string_label = QLabel("String to find:", self)
        self.find_string_label_edit = CustomLine(text="",place_holder_text="String in file name to search, e.g: conf",parent=self)

        # Extension
        self.extension_label = QLabel("Extension type to find:", self)
        self.extension_label_edit = CustomLine(text="",place_holder_text="Extension with the dot, e.g: .txt",parent=self)

        # Checkboxes
        self.match_string_checkbox = QCheckBox("Match string case", self)
        self.is_encrypted_checkbox = QCheckBox("Is Encrypted", self)

        # Search button
        self.search_button = CustomButton("Search", QIcon(ICON_1), "Search for the given file(s) with the checked parameters" ,self)
        self.search_button.clicked.connect(self.search_files)

        # Merge divs
        self.vertical_layout.addWidget(self.find_string_label)
        self.vertical_layout.addWidget(self.find_string_label_edit)
        self.vertical_layout.addWidget(self.extension_label)
        self.vertical_layout.addWidget(self.extension_label_edit)
        self.horizontal_layout.addWidget(self.match_string_checkbox)
        self.horizontal_layout.addWidget(self.is_encrypted_checkbox)
        self.vertical_layout.addLayout(self.horizontal_layout)
        self.vertical_layout.addWidget(self.search_button)

    def search_files(self):
        extension_text = self.extension_label_edit.text()
        string_name_text = self.find_string_label_edit.text()
        match_string_case = self.match_string_checkbox.isChecked()
        is_encrypted = self.is_encrypted_checkbox.isChecked()

        if extension_text == '' and string_name_text == '':
            self.parent().show_message("Incorrect parameters", "At least an extension or a file name should exist.")
            return
        self.hide()
        self.parent().look_for_given_files(string_name_text, extension_text, match_string_case, is_encrypted)
        self.close()
