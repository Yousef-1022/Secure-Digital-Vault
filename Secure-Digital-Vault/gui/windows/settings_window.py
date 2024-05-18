from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QListWidget, QListWidgetItem, QGroupBox, QDialog
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal , Qt

from utils.constants import ICON_1
from utils.parsers import parse_timestamp_to_string, parse_size_to_string

from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_line_password import CustomPasswordLineEdit
from gui.interactions.log_extract_dialog import LogExtractDialog
from gui import VaultView


class SettingsWindow(QMainWindow):

    signal_for_destruction = pyqtSignal(object)

    def __init__(self, parent : VaultView, vault_header : dict, vault_footer : dict):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        # Data
        self.threads = []
        self.__vault_header = vault_header
        self.__ascend = True

        # Central widget and self.horziontal_layout
        self.central_widget = QWidget(self)
        self.vertical_layout = QVBoxLayout(self.central_widget)
        self.horizontal_layout = QHBoxLayout()

        # Split window to Two parts
        self.vertical_layout1 = QVBoxLayout()
        self.vertical_layout2 = QVBoxLayout()
        self.horizontal_sublayout1 = QHBoxLayout()
        self.horizontal_sublayout2 = QHBoxLayout()

        # New Vault Details
        self.input_field_name = CustomLine("", f"New Vault Name", self.central_widget)
        self.input_field_name.set_representing("New Name")
        self.input_field_extension = CustomLine("", f"New Vault Extension with the dot , e.g; .vault", self.central_widget)
        self.input_field_extension.set_representing("New Extension")

        # Password to change the vault password
        self.password_line_old = CustomPasswordLineEdit(placeholder_text="Old Vault Password", icon=QIcon(ICON_1) , parent=self.central_widget)
        self.password_line_new = CustomPasswordLineEdit(placeholder_text="New Vault Password", icon=QIcon(ICON_1) , parent=self.central_widget)
        self.input_field_hint = CustomLine("", f"New Vault Hint", self.central_widget)

        # Buttons related to vertical_layout1
        self.save_vault_information_button = CustomButton("Save",QIcon(ICON_1), "Save details to change the vault information",self.central_widget)
        self.execute_change_button = CustomButton("Execute",QIcon(ICON_1), "Execute the changes for the Vault. Keep the passwords empty if you would like to change basic data only.", self.central_widget)

        # Log List
        self.list_data_log = QListWidget(self)
        for log_whole in vault_footer.values():
            if log_whole:
                individual_logs = [l for l in log_whole.split("\n") if l != '']
                for log in individual_logs:
                    self.list_data_log.addItem(QListWidgetItem(log))
        self.list_data_log.sortItems(Qt.SortOrder.DescendingOrder)

        # Buttons related to vertical_layout2
        self.sort_logs_button = CustomButton("Sort",QIcon(ICON_1), "Sort the logs inside the Vault either in DescendingOrder or AscendingOrder",self.central_widget)
        self.sort_logs_button.set_action(self.sort_logs)
        self.extract_logs_buttons = CustomButton("Extract",QIcon(ICON_1), "Extract the logs out of the Vault", self.central_widget)
        self.extract_logs_buttons.set_action(self.extract_logs)

        # List to show some Vault Information
        self.list_data_vault = QListWidget(self)
        self.list_data_vault.addItem(QListWidgetItem(f"Vault Creation Date: {parse_timestamp_to_string(self.__vault_header['trusted_timestamp'])}"))
        self.list_data_vault.addItem(QListWidgetItem(f"Vault Name: {self.__vault_header['vault_name']}"))
        self.list_data_vault.addItem(QListWidgetItem(f"Vault Extension: {self.__vault_header['vault_extension']}"))
        self.list_data_vault.addItem(QListWidgetItem(f"Amount of Files: {self.__vault_header['amount_of_files']}"))
        self.list_data_vault.addItem(QListWidgetItem(f"Total Size of all Files: {parse_size_to_string(self.__vault_header['file_size'])}"))

        # GroupBox for Regular Settings
        group_box_regular = QGroupBox("Change Vault Details")
        group_box_regular_layout = QVBoxLayout()
        group_box_regular.setLayout(group_box_regular_layout)
        group_box_regular_layout.addWidget(self.input_field_name)
        group_box_regular_layout.addWidget(self.input_field_extension)

        # GroupBox for Password Settings
        group_box_password = QGroupBox("Change Password")
        group_box_password_layout = QVBoxLayout()
        group_box_password.setLayout(group_box_password_layout)
        group_box_password_layout.addWidget(self.password_line_old)
        group_box_password_layout.addWidget(self.password_line_new)
        group_box_password_layout.addWidget(self.input_field_hint)
        self.horizontal_sublayout1.addWidget(self.save_vault_information_button)
        self.horizontal_sublayout1.addWidget(self.execute_change_button)
        group_box_password_layout.addLayout(self.horizontal_sublayout1)

        # GroupBox for Information
        group_box_information = QGroupBox("General Vault Information")
        group_box_information_layout = QVBoxLayout()
        group_box_information.setLayout(group_box_information_layout)
        group_box_information_layout.addWidget(self.list_data_vault)

        # Insert into Left
        self.vertical_layout1.addWidget(group_box_regular)
        self.vertical_layout1.addWidget(group_box_password)
        self.vertical_layout1.addWidget(group_box_information)

        # GroupBox for Logs
        group_box_logs = QGroupBox("Vault Information Logs")
        group_box_logs_layout = QVBoxLayout()
        group_box_logs.setLayout(group_box_logs_layout)
        group_box_logs_layout.addWidget(self.list_data_log)
        self.horizontal_sublayout2.addWidget(self.sort_logs_button)
        self.horizontal_sublayout2.addWidget(self.extract_logs_buttons)
        group_box_logs_layout.addLayout(self.horizontal_sublayout2)

        self.vertical_layout2.addWidget(group_box_logs)

        self.horizontal_layout.addLayout(self.vertical_layout1)
        self.horizontal_layout.addLayout(self.vertical_layout2)
        self.vertical_layout.addLayout(self.horizontal_layout)

        # Progress report
        self.progress_bar = CustomProgressBar(is_visible_at_start=False, parent=self.central_widget)
        self.vertical_layout.addWidget(self.progress_bar)

        # Additional information labels can be added here
        self.setCentralWidget(self.central_widget)

    def sort_logs(self):
        """Sorts the logs in the QListWidget from newest to oldest
        """
        if self.__ascend:
            self.list_data_log.sortItems(Qt.SortOrder.AscendingOrder)
        else:
            self.list_data_log.sortItems(Qt.SortOrder.DescendingOrder)
        self.__ascend = not self.__ascend

    def extract_logs(self):
        """Extracts the logs
        """
        the_logs = b''
        items = [self.list_data_log.item(item).text() for item in range(self.list_data_log.count())]
        for log in items:
            the_logs += (log + "\n").encode()
        dialog = LogExtractDialog(the_logs)
        dialog.exec()
        dialog.deleteLater()

    def update_progress_bar(self, num_to_update_with : int) -> None:
        """Updates the progress bar with the given value

        Args:
            emitted_num (int): Num to add into bar
        """
        if num_to_update_with == 100 or self.progress_bar.value() >= 100:
            self.progress_bar.stop_progress(False)
            return
        current_value = self.progress_bar.value()
        if num_to_update_with + current_value >= 100:
            self.progress_bar.setValue(99)
        else:
            self.progress_bar.setValue(num_to_update_with + current_value)

    def closeEvent(self, event):
        """Override for close window and clean up any remaining items
        """
        print("Settings: Signaled for destruction")
        self.exit()
        self.signal_for_destruction.emit("Destroy")
        super().closeEvent(event)

    def exit(self):
        """Cleans up any available threads and tries to close them along with the window.
        """
        self.clearFocus()
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.hide()
        self.close()
