from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QListWidget, QListWidgetItem, QGroupBox, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal , Qt

from utils.constants import ICON_5, ICON_7, ICON_8, ICON_12, ICON_14, CHUNK_LIMIT
from file_handle.file_io import rename_file, override_bytes_in_file, append_bytes_into_file
from utils.parsers import parse_timestamp_to_string, parse_size_to_string, parse_file_name
from utils.helpers import is_proper_extension
from utils.extractors import get_file_from_vault
from crypto.encryptors import encrypt_bytes, generate_password_token
from crypto.decryptors import decrypt_bytes
from crypto.utils import is_password_strong, generate_aes_key, to_base64

from custom_exceptions.classes_exceptions import DecryptionFailure

from classes.vault import Vault
from logger.logging import Logger
from threads.custom_thread import Worker, CustomThread
from threads.mutable_boolean import MutableBoolean

from gui.custom_widgets.custom_messagebox import CustomMessageBox
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_line_password import CustomPasswordLineEdit
from gui.interactions.log_extract_dialog import LogExtractDialog
from gui import VaultView

from math import ceil, floor
from Crypto.Random import get_random_bytes


class SettingsWindow(QMainWindow):

    signal_for_destruction = pyqtSignal(object)

    def __init__(self, parent : VaultView, vault : Vault, vault_footer : dict):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        # Data
        self.threads = []
        self.__vault = vault
        self.__ascend = True
        self.__new_dict = None
        self.__is_change_password_running = MutableBoolean(False)

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
        self.password_line_old = CustomPasswordLineEdit(placeholder_text="Old Vault Password", icon=QIcon(ICON_7) , parent=self.central_widget)
        self.password_line_new = CustomPasswordLineEdit(placeholder_text="New Vault Password", icon=QIcon(ICON_7) , parent=self.central_widget)
        self.input_field_hint = CustomLine("", f"New Vault Hint", self.central_widget)

        # Buttons related to vertical_layout1
        self.save_vault_information_button = CustomButton("Save",QIcon(ICON_5), "Save details to change the vault information",self.central_widget)
        self.save_vault_information_button.set_action(self.save_details)

        self.execute_change_button = CustomButton("Execute",QIcon(ICON_8), "Execute the changes for the Vault. Keep the passwords empty if you would like to change basic data only.", self.central_widget)
        self.execute_change_button.setDisabled(True)
        self.execute_change_button.set_action(self.update_vault)

        # Log List
        self.list_data_log = QListWidget(self)
        for log_whole in vault_footer.values():
            if log_whole:
                individual_logs = [l for l in log_whole.split("\n") if l != '']
                for log in individual_logs:
                    self.list_data_log.addItem(QListWidgetItem(log))
        self.list_data_log.sortItems(Qt.SortOrder.DescendingOrder)

        # Buttons related to vertical_layout2
        self.sort_logs_button = CustomButton("Sort",QIcon(ICON_14), "Sort the logs inside the Vault either in DescendingOrder or AscendingOrder",self.central_widget)
        self.sort_logs_button.set_action(self.sort_logs)
        self.extract_logs_buttons = CustomButton("Extract",QIcon(ICON_12), "Extract the logs out of the Vault", self.central_widget)
        self.extract_logs_buttons.set_action(self.extract_logs)

        # List to show some Vault Information
        header = self.__vault.get_header()
        self.list_data_vault = QListWidget(self)
        self.list_data_vault.addItem(QListWidgetItem(f"Vault Creation Date: {parse_timestamp_to_string(header['vault']['trusted_timestamp'])}"))
        self.list_data_vault.addItem(QListWidgetItem(f"Vault Name: {header['vault']['vault_name']}"))
        self.list_data_vault.addItem(QListWidgetItem(f"Vault Extension: {header['vault']['vault_extension']}"))
        self.list_data_vault.addItem(QListWidgetItem(f"Amount of Files: {header['vault']['amount_of_files']}"))
        self.list_data_vault.addItem(QListWidgetItem(f"Total Size of all Files: {parse_size_to_string(header['vault']['file_size'])}"))

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

    def __lock_details_change(self, lock : bool):
        """Locks the buttons related to the vault change according to the boolean value

        Args:
            lock (bool): True if to Lock, False to Unlock
        """
        self.input_field_name.setDisabled(lock)
        self.input_field_extension.setDisabled(lock)
        self.input_field_hint.setDisabled(lock)
        self.password_line_new.get_passwordLine().setDisabled(lock)
        self.password_line_old.get_passwordLine().setDisabled(lock)
        self.execute_change_button.setEnabled(lock)

    def check_vault_details(self) -> tuple[bool,dict]:
        """Confirms whether the details are valid

        Returns:
            tuple[bool,dict]: [0] represents whether everything was valid
        """
        errors = ""
        new_extension = self.input_field_extension.text()
        if new_extension != '' and not is_proper_extension(new_extension):
            errors += f"- The extension {new_extension} is invalid! Valid example: '.vault'.\n"

        new_name = self.input_field_name.text()
        res = parse_file_name(new_name)
        if not res[0]:
            errors += f'- {res[1]}\n'

        old_password = self.password_line_old.get_passwordLine().text()
        new_password = self.password_line_new.get_passwordLine().text()
        new_hint = self.input_field_hint.text()

        if old_password != '' and new_password != '':
            original_password = self.parent().request_vault_password()
            if original_password != old_password:
                errors += f"- The given password '{old_password}' is not associated with this Vault!\n"
            res = is_password_strong(new_password)
            if not res[0]:
                for error in res[1]:
                    errors += f'- {error}\n'
            if original_password == new_password:
                errors += f"- Use a different password than '{new_password}'\n"
            if new_hint == '':
                errors += "- New hint cannot be empty if setting a password!\n"
            elif len(new_hint) > 32:
                errors += "- The hint must be less than 32 characters!\n"

        if new_extension == '' and new_name == '' and old_password == '':
            errors += '- Nothing to execute. Write a change\n'

        if len(errors) != 0:
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Vault Update Data")
            message_box.showMessage(errors)
            return False , {}
        res = {
            'new_name' : new_name,
            'new_extension' : new_extension,
            'new_hint' : new_hint,
            'new_password' : new_password
        }
        return True , res

    def save_details(self):
        """Checks the details, Flips the Save button into Edit and vice versa, only with this its allowed to execute.
        """
        if self.save_vault_information_button.text() == "Save":
            res = self.check_vault_details()
            if res[0]:
                self.__lock_details_change(True)
                self.__new_dict = res[1]
            else:
                return
            self.save_vault_information_button.setText("Edit")
        else:
            self.__new_dict = None
            self.__lock_details_change(False)
            self.save_vault_information_button.setText("Save")

    def update_vault(self):
        """Updates the vault with the given details
        """
        if self.save_vault_information_button.text() == "Save":
            return

        # Vault Details First
        logger = Logger()
        header = self.__vault.get_header()
        old_name = header["vault"]["vault_name"]
        old_extension = header["vault"]["vault_extension"]

        # Name
        if self.__new_dict["new_name"]:
            header["vault"]["vault_name"] = self.__new_dict["new_name"]
        if self.__new_dict["new_extension"]:
            header["vault"]["vault_extension"] = self.__new_dict["new_extension"]

        vault_name = header["vault"]["vault_name"] + header["vault"]["vault_extension"]

        if self.__new_dict["new_name"] or self.__new_dict["new_extension"]:
            res = rename_file(self.__vault.get_vault_path(), vault_name)
            if not res[0]:
                header["vault"]["vault_name"] = old_name
                header["vault"]["vault_extension"] = old_extension
                message_box = CustomMessageBox(parent=self)
                message_box.setIcon(QMessageBox.Icon.Warning)
                message_box.setWindowTitle("Vault Update Data")
                message_box.showMessage(f"Failure to rename: {res[1]}")
                return
            cur_path = self.__vault.get_vault_path()
            cur_path = f'{cur_path[:cur_path.rfind("/")]}/{res[1]}'
            self.__vault.set_vault_path(cur_path)
            self.parent().statusBar().showMessage(f"You're viewing the Vault: {self.__vault.get_vault_path()}")
            logger.attention(f"Renamed vault to: {vault_name}")
        if not self.__new_dict['new_password']:
            return
        self.__vault.set_hint(self.__new_dict['new_hint'])

        # Thread for new Vault
        self.mythread = CustomThread(240 , self.update_vault.__name__)
        self.worker = Worker(self.__change_password, self.__vault.get_password(), self.__new_dict['new_password'], self.__vault)
        self.worker.args += (self.worker.progress, )    # Force add signal

        self.worker.progress.connect(self.update_progress_bar)
        self.worker.moveToThread(self.mythread)
        self.mythread.started.connect(self.worker.run)

        def __end_worker_activity(emitted_result):
            self.mythread.stop_timer(emit_finish=False, emitted_result=emitted_result)
            self.worker.deleteLater()
        self.worker.finished.connect(__end_worker_activity)

        def __end_thread_activity():
            self.__vault.set_password(self.__new_dict['new_password'])
            self.__update_header()  # After import, the vault must have saved information.
            self.__is_change_password_running.set_value(False)
            logger.attention("Successfully changed Vault password and hint!")
            self.execute_change_button.setEnabled(True)
            self.save_vault_information_button.setEnabled(True)
            self.__token_activity(self.__vault.get_password(), self.__vault.get_vault_path())
            self.mythread.quit()
        self.mythread.timeout_signal.connect(__end_thread_activity)
        self.mythread.finished.connect(self.mythread.deleteLater)

        self.progress_bar.setVisible(True)
        self.__is_change_password_running.set_value(True)
        self.execute_change_button.setEnabled(False)
        self.save_vault_information_button.setEnabled(False)
        self.threads.append(self.mythread)
        self.mythread.start()

    def __token_activity(self, password : str, location_for_tokens : str):
        """Generates the tokens and notifies the user that everything was successful

        Args:
            password (str): The new passaword
            location_for_tokens (str): The location for the tokens
        """
        location_for_tokens = location_for_tokens[:location_for_tokens.rfind("/")]
        self.__generate_tokens(password, location_for_tokens)
        self.message_box = CustomMessageBox(parent=self)
        self.message_box.setIcon(QMessageBox.Icon.Information)
        self.message_box.setWindowTitle("Vault Special Tokens")
        self.message_box.showMessage(f"Please find the new special Vault tokens which can be used as recovery in {location_for_tokens}/tokens.txt")
        self.message_box.deleteLater()
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def __update_header(self) -> None:
        """Refreshes the header, and modifies the vault itself.
        """
        self.__vault.refresh_header()
        self.__vault.update_vault_file()

    def __change_password(self, old_password : str, new_password :str, vault : Vault, progress_signal : pyqtSignal) -> None:
        """Updates the Vault with the new Password. This process cannot be aborted.

        Args:
            old_password (str): The original password of the Vault
            new_password (str): The new password
            vault (Vault): The Vault itself.
            progress_signal (pyqtsignal): Signal to update the progress bar
        """
        logger = Logger()
        file_ids = self.__vault.get_map()['file_ids']
        files = self.__vault.get_map()['files']

        file_amount = len(file_ids)
        cntr = emitted = 0
        emit_every = 1

        if file_amount > 100:
            emit_every = floor(file_amount / 100)
        else:
            emit_every = ceil(100 / file_amount)

        for f in file_ids:
            file = files[str(f)]
            full_file_name = f"{file['metadata']['name']}.{file['metadata']['type']}"
            file_from_vault = get_file_from_vault(vault.get_vault_path(), file['loc_start'], file['loc_end'])
            res = file_from_vault
            old_size = len(res)
            # File must not be empty when decrypting
            # Regular decryption
            if res:
                try:
                    # Large File Scenario
                    if len(res) > CHUNK_LIMIT:
                        salt = res[:16]
                        iv = res[16:32]
                        key = generate_aes_key(password=old_password.encode(), salt=salt, key_length=32)
                        res = res[32:]
                        decrypted_bytes = bytearray()
                        while True:
                            move_amount = CHUNK_LIMIT + 16 # Account for padding overhead
                            chunk = res[:move_amount]
                            if not chunk:
                                break
                            decrypted_chunk = decrypt_bytes(ciphertext=chunk, password='', key=key, iv=iv)
                            decrypted_bytes.extend(decrypted_chunk)
                            # Move Array
                            res = res[move_amount:]
                            if len(res) == 0:
                                break
                        res = bytes(decrypted_bytes)
                    # Small File Scenario
                    else:
                        res = decrypt_bytes(res, old_password)
                except DecryptionFailure as e:
                    logger.error(f"Unexpected Vault Failure for {full_file_name}. Error: {e}. Retry action after reopening the Vault")
                    continue
            else:
                logger.warn(f"Unexpected Vault Failure for {full_file_name} because getting it from the Vault returned empty")

            # Encrypting a large file, must add salt_iv first, then add the encrypted data
            encrypted_file = None
            if len(res) > CHUNK_LIMIT:
                # Encryption Data
                salt = get_random_bytes(16)
                iv = get_random_bytes(16)
                salt_iv = salt + iv
                key = generate_aes_key(password=new_password.encode(), salt=salt, key_length=32)

                # Helper Variables
                read_bytes = 0
                encrypted_bytes = bytearray()
                encrypted_bytes.extend(salt_iv)

                while True:
                    move_amount = CHUNK_LIMIT
                    chunk = res[:move_amount]
                    if len(chunk) == 0:
                        break
                    read_bytes+=move_amount
                    encrypted_chunk = encrypt_bytes(data=chunk, password=new_password, key=key, iv=iv)
                    encrypted_bytes.extend(encrypted_chunk)
                    res = res[move_amount:]
                    if len(res) == 0:
                        break
                encrypted_file = bytes(encrypted_bytes)
                if old_size != len(encrypted_file):
                    # Failure example shouldn't happen.
                    logger.error(f'File: {full_file_name} length is not the same after re-encrypt. {len(encrypted_file)} != {old_size}')
            # Small File Scenario
            else:
                encrypted_file = encrypt_bytes(data=res, password=new_password)
            fd = override_bytes_in_file(file_path=vault.get_vault_path(), given_bytes=encrypted_file, byte_loss=0, at_location=file['loc_start'])
            if fd:
                fd.close()
            cntr+=1

            # ProgressBar
            if file_amount > 100:
                if cntr == emit_every:
                    progress_signal.emit(1)
                    cntr = 0
                    emitted+=1
            else:
                if emitted + emit_every < 100:
                    progress_signal.emit(emit_every)
                    emitted+=emit_every
        progress_signal.emit(100)

    def __generate_tokens(self, password : str, location_for_tokens : str):
        """Generates the Vault Recovery tokens

        Args:
            password (str): The password
            location_for_tokens (str): The path for the tokens
        """
        token1 = to_base64(generate_password_token(password))
        token2 = to_base64(generate_password_token(password))
        token3 = to_base64(generate_password_token(password))
        tokens = f'1: {token1}\n2: {token2}\n3: {token3}\n'.encode()
        append_bytes_into_file(location_for_tokens, tokens, create_file=True, file_name='tokens.txt')

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
        if self.__is_change_password_running.get_value():
            event.ignore()
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Passowrd change is running")
            message_box.showMessage("Vault is undergoing password change, cannot close this right now!")
        else:
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
