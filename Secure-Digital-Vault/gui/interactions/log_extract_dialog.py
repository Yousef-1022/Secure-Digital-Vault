from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QMessageBox
from PyQt6.QtGui import QIcon

from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_messagebox import CustomMessageBox

from logger.logging import Logger
from file_handle.file_io import append_bytes_into_file
from utils.constants import ICON_10, ICON_12

class LogExtractDialog(QDialog):

    def __init__(self, log_bytes : bytes , parent = None):
        super().__init__(parent)

        self.setWindowTitle("Extract Logs")
        self.setWindowIcon(QIcon(ICON_12))

        self.__logs = log_bytes
        self.vertical_layout = QVBoxLayout(self)
        self.horizontal_layout = QHBoxLayout()

        self.file_location_label = QLabel("Location to put the logs in", self)
        self.file_location_label_edit = CustomLine(text="",place_holder_text="/path/to/file",parent=self)

        self.export_button = CustomButton("Export", QIcon(ICON_10), "Get all the logs associated with Vault into the given location" ,self)
        self.export_button.set_action(self.export_logs)

        self.vertical_layout.addWidget(self.file_location_label)
        self.vertical_layout.addWidget(self.file_location_label_edit)
        self.vertical_layout.addWidget(self.export_button)

    def export_logs(self):
        res = append_bytes_into_file(file_path=self.file_location_label_edit.text(), the_bytes=self.__logs,
                               create_file=True, file_name="logs.txt")
        if not res[0]:
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Invalid location")
            message_box.showMessage(f"The given location: '{self.file_location_label_edit.text()}' is not valid because '{res[1]}'!")
            message_box.close()
            message_box.deleteLater()
            return
        self.hide()
        self.close()
        logger = Logger()
        logger.info("Logs extracted by request")
