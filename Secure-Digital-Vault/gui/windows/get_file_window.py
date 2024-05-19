from PyQt6.QtWidgets import QVBoxLayout, QMainWindow, QWidget, QListWidget, QListWidgetItem, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, QDir
from PyQt6.QtGui import QIcon

from classes.directory import Directory
from classes.file import File
from custom_exceptions.classes_exceptions import DecryptionFailure
from logger.logging import Logger

from utils.constants import ICON_1, CHUNK_LIMIT
from utils.helpers import get_available_drives, is_location_ok
from utils.parsers import show_as_windows_directory
from utils.extractors import get_file_from_vault
from file_handle.file_io import create_folder_on_disk, append_bytes_into_file
from crypto.decryptors import decrypt_bytes
from crypto.utils import generate_aes_key, get_checksum
from math import floor, ceil

from gui import VaultView
from threads.custom_thread import CustomThread, Worker
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.interactions.interact_dialog import InteractDialog

import time


# Can be used for both files and folders.
class GetFileWindow(QMainWindow):

    signal_for_destruction = pyqtSignal(str)

    def __init__(self, parent : VaultView, items : list[CustomQTreeWidgetItem]):
        super().__init__(parent)
        self.setWindowTitle("Extract Items")
        self.setMinimumSize(600, 400)
        self.items = items

        # Custom Data
        self.threads = []
        self.__vault_loc = self.parent().request_vault_path()
        self.__vault_pass = self.parent().request_vault_password()
        self.__dialog = InteractDialog(self)
        self.__interactable = [False, "Skip", ""]

        # Central widget and self.vertical_layout
        self.central_widget = QWidget(self)
        self.vertical_layout = QVBoxLayout(self.central_widget)
        self.horizontal_layout = QHBoxLayout()

        # It contains the list of highlighted items
        self.list_widget = QListWidget(self)
        for item in self.items:
            element = QListWidgetItem()
            element.setText(item.get_saved_obj().__str__())
            element.setIcon(item.icon(0))
            self.list_widget.addItem(element)

        # Location label
        self.address_bar = CustomLine(text="", place_holder_text="Path on disk, e.g, D:/path/to/", parent=self.central_widget)
        self.address_bar.returnPressed.connect(lambda : self.on_extract_button_clicked())
        self.extract_button = CustomButton("Extract",QIcon(ICON_1), "Extract the items from the vault without deleting them",self.central_widget)
        self.extract_button.set_action(self.on_extract_button_clicked)

        # Progress report
        self.extraction_progress_bar = CustomProgressBar(is_visible_at_start=False, parent=self.central_widget)

        # Merge layouts
        self.horizontal_layout.addWidget(self.address_bar)
        self.horizontal_layout.addWidget(self.extract_button)

        self.vertical_layout.addWidget(self.list_widget)
        self.vertical_layout.addWidget(self.extraction_progress_bar)
        self.vertical_layout.addLayout(self.horizontal_layout)

        # Additional information labels can be added here
        self.setCentralWidget(self.central_widget)

    def on_extract_button_clicked(self):
        """When the extract button is pressed, get the items from the vault.
        """
        path = self.address_bar.text()
        if not path:
            return
        directory = QDir(path)
        drive = path[0] + ":\\" # Edge case when drive is only selected, first letter is taken
        if not directory.exists() or (drive not in get_available_drives()) or (len(path) < 3):
            window_title = "Unknown location"
            message = f"Could not find the path {path} on the system!"
            self.parent().show_message(window_title=window_title, message=message, parent=self)
            return

        res = is_location_ok(location_path=path, for_file_save=True, for_file_update=False)
        if not res[0]:
            window_title = "Location Problem"
            message = f"Could not save a file in the path {path} on the system. Reason: {res[1]}"
            self.parent().show_message(window_title=window_title, message=message, parent=self)
            return

        # Extraction Logic, we get all files and modify their paths for easier disk insertion

        all_files = []
        for item in self.items:
            if isinstance(item.get_saved_obj(), File):
                full_path = self.parent().request_path_string(the_id = "/", full_path = False, type = "F")
                item.get_saved_obj().set_path(full_path)
                all_files.append(item.get_saved_obj())
            elif isinstance(item.get_saved_obj(), Directory):
                res = self.parent().request_files_from_vault(item.get_saved_obj().get_id(), False, item.get_saved_obj().get_name()) # Must get initial parent
                all_files.extend(res)
        dir_loc = show_as_windows_directory(path)

        # Threading
        self.mythread = CustomThread(240 , self.on_extract_button_clicked.__name__)
        self.threads.append(self.mythread)

        self.worker = Worker(self.process_extract, all_files, dir_loc, self.__vault_loc, self.__vault_pass, self.__interactable)
        self.worker.args += (self.worker.interaction, )
        self.worker.args += (self.worker.progress, )    # Force add signals

        self.worker.interaction.connect(self.interaction_function)
        self.worker.progress.connect(self.update_extract_progress)
        self.worker.moveToThread(self.mythread)
        self.mythread.started.connect(self.worker.run)

        def __end_worker_activity(emitted_result):
            self.mythread.stop_timer(emit_finish=False, emitted_result=emitted_result)
            self.worker.deleteLater()
        self.worker.finished.connect(__end_worker_activity)

        def __end_thread_activity():
            self.extraction_progress_bar.setValue(0)
            self.extraction_progress_bar.setVisible(False)
            self.address_bar.setEnabled(True)
            self.mythread.quit()
        self.mythread.timeout_signal.connect(__end_thread_activity)
        self.mythread.finished.connect(self.mythread.deleteLater)

        self.extraction_progress_bar.setVisible(True)
        self.address_bar.setDisabled(True)
        self.mythread.start()

    def update_extract_progress(self, num_to_update_with : int) -> None:
        """Updates the extraction progress bar with the given value

        Args:
            emitted_num (int): Num to add into bar
        """
        if num_to_update_with == 100 or self.extraction_progress_bar.value() >= 100:
            self.extraction_progress_bar.stop_progress(False)
            return
        current_value = self.extraction_progress_bar.value()
        if num_to_update_with + current_value >= 100:
            self.extraction_progress_bar.setValue(99)
        else:
            self.extraction_progress_bar.setValue(num_to_update_with + current_value)

    def process_extract(self, lst : list[File], address_location : str, vault_loc : str, vault_password : str, interactable_item : object,
                        interaction_signal : pyqtSignal, progress_signal : pyqtSignal):
        """Starts the extraction process of the given items in the list

        Args:
            lst (list[File]): The items to extract, this lists consists of Files.
            address_location (str): The folder location to add the items into, e.g: D:\\Path\\To\\
            vault_loc (str): The location of the vault
            vault_password (str): The password used to unlock the vault
            interactable_item(object): The item passed around by the itneraction signal
            interaction_signal(pyqtSignal): Signal to interact with the main thread
            progress_signal (pyqtSignal): Signal to emit for the progress bar to increase
        """
        file_amount = len(lst)
        cntr = emitted = 0
        emit_every = 1

        if file_amount > 100:
            emit_every = floor(file_amount / 100)
        else:
            emit_every = ceil(100 / file_amount)
        logger = Logger()

        for file in lst:
            password = None

            # Check if file encrypted, open dialog:
            if file.get_file_encrypted():
                # Set interactable object data. 0 = KeepRunning (bool), 1 = RequestType (str), 2 = Name (str)
                interactable_item[0] = True         # Keep running
                interactable_item[1] = "Password"   # Request
                if file.get_path() == "/":
                    interactable_item[2] = f'{file.get_metadata()["name"]}.{file.get_metadata()["type"]}'
                else:
                    interactable_item[2] = file.get_path() + f'{file.get_metadata()["name"]}.{file.get_metadata()["type"]}'
                interaction_signal.emit(interactable_item)

                while interactable_item[0] == True:
                    time.sleep(1)   # Wait for response

                if interactable_item[1] == "Skip":
                    at_path = file.get_path()
                    logger.info(f"Skipped: {'' if at_path == '/' else at_path}{file.get_metadata()['name']}.{file.get_metadata()['type']}")
                    if file_amount > 100:
                        if cntr == emit_every:
                            progress_signal.emit(1)
                            cntr = 0
                            emitted+=1
                    else:
                        if emitted + emit_every < 100:
                            progress_signal.emit(emit_every)
                            emitted+=emit_every
                    continue
                elif interactable_item[1] == "Proceed":
                    password = interactable_item[2]
                interactable_item[0] = False
                interactable_item[1] = "Skip"
                interactable_item[2] = ""

            # Folder on disk creation
            cntr+=1
            full_file_name  = f'{file.get_metadata()["name"]}.{file.get_metadata()["type"]}'
            folder_location = address_location + file.get_path().replace("/","\\")
            res = create_folder_on_disk(folder_location)
            if not res:
                logger.error(f"Couldn't create location: {folder_location}")
                continue
            file_from_vault = get_file_from_vault(vault_loc, file.get_loc_start(), file.get_loc_end())
            res = file_from_vault
            # File must not be empty when decrypting
            if res:
                # Regular decryption
                try:
                    # Large File Scenario
                    if len(res) > CHUNK_LIMIT:
                        salt = res[:16]
                        iv = res[16:32]
                        key = generate_aes_key(password=vault_password.encode(), salt=salt, key_length=32)
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
                        res = decrypt_bytes(res, vault_password)
                except DecryptionFailure as e:
                    logger.error(f"Unexpected Vault Failure for {full_file_name}. Error: {e}. Retry action after reopening the Vault")
                    continue
                # If file is encrypted
                if password:
                    try:
                        res = decrypt_bytes(res, password)
                    except DecryptionFailure as e:
                        logger.warn(f"Password incorrect for {full_file_name}")
                        continue

            output_checksum = get_checksum(res, is_file=False)
            res = append_bytes_into_file(folder_location, res, create_file=True, file_name=full_file_name)
            if file.get_checksum() != output_checksum:
                logger.error(f"Saved file checksum {file.get_checksum()} does not correspond to what was taken from the Vault {output_checksum}")

            # Extract Note:
            if file.get_metadata()["note_id"] != -1:
                self.parent().get_note_from_vault(folder_location, file.get_metadata()["note_id"], False)

            if file_amount > 100:
                if cntr == emit_every:
                    progress_signal.emit(1)
                    cntr = 0
                    emitted+=1
            else:
                if emitted + emit_every < 100:
                    progress_signal.emit(emit_every)
                    emitted+=emit_every
            logger.info(f"Finished extracting {full_file_name}")

        progress_signal.emit(100)

    def interaction_function(self):
        """Function used to communicate with the subthread in order to grab the password
        """
        if self.__interactable[1] == "Password":
            self.__dialog.password_string_label.setText(f"File {self.__interactable[2]} is encrypted! Password:")
            self.__interactable[1] = "Skip"
            self.__interactable[2] = ""
            self.__dialog.exec()
        self.__interactable[0] = False                          # KeepRunning (bool)
        self.__interactable[1] = self.__dialog.get_command()    # RequestType (str)
        self.__interactable[2] = self.__dialog.get_data()       # Name (str)
        self.__dialog.reset_inner_items()
        self.__dialog.close()

    def closeEvent(self, event):
        """Override for close window and clean up any remaining items
        """
        self.__dialog.reset_inner_items()
        self.__dialog.close()
        self.__dialog.deleteLater()
        self.exit()
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
        self.signal_for_destruction.emit("Destroy")