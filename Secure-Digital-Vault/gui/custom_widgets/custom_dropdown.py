from PyQt6.QtWidgets import QComboBox, QWidget
from utils.helpers import get_available_drives
import os


class CustomDropdown(QComboBox):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.drives = get_available_drives()
        current_drive = f'{os.getcwd()[0]}:\\'
        if current_drive in self.drives:
            self.addItem(current_drive)
            self.drives.remove(current_drive)
        for drive in self.drives:
            self.addItem(drive)
