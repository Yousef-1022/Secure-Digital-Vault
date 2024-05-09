from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line import CustomLine
from gui import VaultView

from utils.constants import ICON_1
from utils.helpers import is_proper_extension, get_file_size
from utils.parsers import parse_size_to_string
from utils.extractors import extract_extension


class AddVoiceDialog(QDialog):

    finished_signal = pyqtSignal(dict)

    def __init__(self, file_id : int, parent: VaultView):
        super().__init__(parent)
        self.setWindowTitle("Add Note")

        self.__file_id = file_id

        self.vertical_layout = QVBoxLayout(self)
        self.horizontal_layout = QHBoxLayout()

        self.file_location_label = QLabel("Location of the file", self)
        self.file_location_label_edit = CustomLine(text="",place_holder_text="/path/to/file",parent=self)

        # Extension
        self.extension_label = QLabel("Extension type:", self)
        self.extension_label_edit = CustomLine(text="",place_holder_text="Extension with the dot, e.g: .mp3",parent=self)

        # Import button
        self.import_button = CustomButton("Import", QIcon(ICON_1), "Add the given file as a note" ,self)
        self.import_button.set_action(self.import_note)

        # Merge divs
        self.vertical_layout.addWidget(self.file_location_label)
        self.vertical_layout.addWidget(self.file_location_label_edit)
        self.vertical_layout.addWidget(self.extension_label)
        self.vertical_layout.addWidget(self.extension_label_edit)
        self.vertical_layout.addWidget(self.import_button)

    def import_note(self):
        extension = self.extension_label_edit.text()
        file_location = self.file_location_label_edit.text()
        if not is_proper_extension(extension):
            self.parent().show_message("Incorrect extension", f"The given extension: '{extension}' is not valid")
            return
        if extract_extension(file_location) != extension[1:]:
            print(file_location,extension,extract_extension(file_location))
            self.parent().show_message("Mistmatch", f"The given extension: '{extension}' does not match what is in the given location: '{file_location}'!")
            return
        res = get_file_size(file_location)
        if res[0] <= 0:
            self.parent().show_message("Invalid file", f"The given location: '{file_location}' is not valid because: '{res[1]}'")
            return
        if res[0] > 10485760:  # 10 MB limit of a note
            self.parent().show_message("Too big", f"The given location: '{file_location}' file is not suitable because the size: '{parse_size_to_string(res[0])}' is bigger than: '{parse_size_to_string(10485760)}'!")
            return
        self.hide()
        self.parent().add_note_to_vault(file_location, extension, self.__file_id)
        self.close()
