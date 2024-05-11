from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QIcon
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line import CustomLine
from gui import VaultView

from utils.constants import ICON_1, NOTE_LIMIT
from utils.helpers import is_proper_extension, get_file_size, is_location_ok
from utils.parsers import parse_size_to_string, show_as_windows_directory
from utils.extractors import extract_extension


class VoiceDialog(QDialog):

    def __init__(self, obj_id : int, parent: VaultView, add_voice : bool = True):
        super().__init__(parent)


        self.setWindowTitle("Add Note")
        if not add_voice:
            self.setWindowTitle("Get Note")

        self.__obj_id = obj_id

        self.vertical_layout = QVBoxLayout(self)
        self.horizontal_layout = QHBoxLayout()

        self.file_location_label = QLabel("Location of the file", self)
        self.file_location_label_edit = CustomLine(text="",place_holder_text="/path/to/file",parent=self)
        if not add_voice:
            self.file_location_label.setText("Location to put the note in")

        # Extension
        if add_voice:
            self.extension_label = QLabel("Extension type:", self)
            self.extension_label_edit = CustomLine(text="",place_holder_text="Extension with the dot, e.g: .mp3",parent=self)

        # Import button
        if add_voice:
            self.import_button = CustomButton("Import", QIcon(ICON_1), "Add the given file as a note" ,self)
            self.import_button.set_action(self.import_note)
        else:
            self.import_button = CustomButton("Get", QIcon(ICON_1), "Get the note of the given file" ,self)
            self.import_button.set_action(self.get_note)

        # Merge divs
        self.vertical_layout.addWidget(self.file_location_label)
        self.vertical_layout.addWidget(self.file_location_label_edit)
        if add_voice:
            self.vertical_layout.addWidget(self.extension_label)
            self.vertical_layout.addWidget(self.extension_label_edit)
        self.vertical_layout.addWidget(self.import_button)

    def import_note(self):
        extension = self.extension_label_edit.text()
        file_location = self.file_location_label_edit.text()
        if not is_proper_extension(extension):
            self.parent().show_message("Incorrect extension", f"The given extension: '{extension}' is not valid", parent=self)
            return
        if extract_extension(file_location) != extension[1:]:
            print(file_location,extension,extract_extension(file_location))
            self.parent().show_message("Mistmatch", f"The given extension: '{extension}' does not match what is in the given location: '{file_location}'!", parent=self)
            return
        res = get_file_size(file_location)
        if res <= 0:
            self.parent().show_message("Invalid file", f"The given location: '{file_location}' is not valid because the size is: '{res}'!", parent=self)
            return
        if res > NOTE_LIMIT:
            self.parent().show_message("Too big", f"The file in the given location: '{file_location}' is not suitable because the size: '{parse_size_to_string(res)}' is bigger than: '{parse_size_to_string(NOTE_LIMIT)}'!", parent=self)
            return
        self.hide()
        self.parent().add_note_to_vault(file_location, extension[1:], self.__obj_id)
        self.close()

    def get_note(self):
        file_location = self.file_location_label_edit.text()
        res = is_location_ok(file_location, for_file_save=True, for_file_update=False)
        if not res[0]:
            self.parent().show_message("Invalid location", f"The given location: '{file_location}' is not valid because '{res[1]}'!", parent=self)
            return
        self.hide()
        self.parent().get_note_from_vault(show_as_windows_directory(file_location), self.__obj_id)
        self.close()
