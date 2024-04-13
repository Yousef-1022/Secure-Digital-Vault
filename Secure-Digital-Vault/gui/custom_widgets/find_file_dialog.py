from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QLabel, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line import CustomLine

from utils.constants import ICON_1

class FindFileDialog(QDialog):

    finished_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
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
        self.match_extension_checkbox = QCheckBox("Match extension case", self)
        self.skip_encrypted_checkbox = QCheckBox("Skip encrypted", self)

        # Search button
        self.search_button = CustomButton("Search", QIcon(ICON_1), "Search for the given file(s) with the checked parameters" ,self)
        self.search_button.clicked.connect(self.search_files)

        # Merge divs
        self.vertical_layout.addWidget(self.find_string_label)
        self.vertical_layout.addWidget(self.find_string_label_edit)
        self.vertical_layout.addWidget(self.extension_label)
        self.vertical_layout.addWidget(self.extension_label_edit)
        self.horizontal_layout.addWidget(self.match_string_checkbox)
        self.horizontal_layout.addWidget(self.match_extension_checkbox)
        self.vertical_layout.addLayout(self.horizontal_layout)
        self.vertical_layout.addWidget(self.skip_encrypted_checkbox)
        self.vertical_layout.addWidget(self.search_button)

    def search_files(self):
        extension_text = self.extension_label_edit.text()
        string_name_text = self.find_string_label_edit.text()
        match_string_case = self.match_string_checkbox.isChecked()
        match_extension_case = self.match_extension_checkbox.isChecked()
        skip_encrypted = self.skip_encrypted_checkbox.isChecked()

        # Perform the search based on the entered text and options
        print("Searching for string:", string_name_text)
        print("Searching for extension:", extension_text)
        print("Match string case:", match_string_case)
        print("Match extension case:", match_extension_case)
        print("Skip encrypted:", skip_encrypted)
        # Emit a signal or perform the search action
        # TODO show the new window of searching for a file.
        self.close()
