from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QListWidget, QListWidgetItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal

from classes.file import File
from classes.directory import Directory

from utils.constants import ICON_1
from utils.parsers import parse_timestamp_to_string
from utils.extractors import get_file_from_vault
from file_handle.file_io import override_bytes_in_file
from crypto.utils import is_password_strong
from crypto.encryptors import encrypt_bytes
from crypto.decryptors import decrypt_bytes

from threads.custom_thread import Worker, CustomThread
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui.interactions.note_dialog import NoteDialog
from gui.interactions.interact_dialog import InteractDialog
from gui import VaultView


class ViewFileWindow(QMainWindow):

    signal_for_destruction = pyqtSignal(object)

    def __init__(self, parent : VaultView, item : CustomQTreeWidgetItem):
        super().__init__(parent)
        self.setWindowTitle("View Item")
        self.setMinimumSize(600, 400)

        # Data
        self.threads = []
        self.__item = item
        self.__encrypted = False
        self.__dialog = InteractDialog(self)
        self.item_updated = False

        # Central widget and self.vertical_layout
        self.central_widget = QWidget(self)
        self.vertical_layout = QVBoxLayout(self.central_widget)

        # Add buttons
        self.button_layout = QHBoxLayout()
        self.encrypt_button = CustomButton("Encrypt", QIcon(ICON_1), "Encrypt file", self.central_widget)
        self.encrypt_button.set_action(self.__encrypt_or_decrypt_file, True)
        self.decrypt_button = CustomButton("Decrypt", QIcon(ICON_1), "Decrypt file", self.central_widget)
        self.decrypt_button.set_action(self.__encrypt_or_decrypt_file, False)

        self.remove_note_button = CustomButton("Remove Note", QIcon(ICON_1), "Remove note note from file", self.central_widget)

        self.add_note_button = CustomButton("Add Note", QIcon(ICON_1), "Add note to file", self.central_widget)
        self.add_note_button.set_action(self.__add_note)
        self.get_note_button = CustomButton("Get Note", QIcon(ICON_1), "Get the Note", self.central_widget)
        self.get_note_button.set_action(self.__get_note)

        # List widget to display items
        self.list_widget = QListWidget(self)
        self.__fullfill_list()

        # Progress report
        self.progress_bar = CustomProgressBar(is_visible_at_start=False, parent=self.central_widget)

        # Add buttons to self.vertical_layout
        self.button_layout.addWidget(self.encrypt_button)
        self.button_layout.addWidget(self.decrypt_button)
        self.button_layout.addWidget(self.remove_note_button)
        self.button_layout.addWidget(self.add_note_button)
        self.button_layout.addWidget(self.get_note_button)
        self.vertical_layout.addLayout(self.button_layout)
        self.vertical_layout.addWidget(self.list_widget)
        self.vertical_layout.addWidget(self.progress_bar)

        # Panel self.vertical_layout for bottom left
        panel_layout = QHBoxLayout()
        self.vertical_layout.addLayout(panel_layout)

        # Additional information labels can be added here
        self.setCentralWidget(self.central_widget)

    def __update_buttons(self):
        """Updates the buttons according to the data of the item
        """
        if isinstance(self.__item.get_saved_obj(), File):
            if self.__item.get_saved_obj().get_file_encrypted():
                self.encrypt_button.setDisabled(True)
                self.decrypt_button.setEnabled(True)
            else:
                self.encrypt_button.setEnabled(True)
                self.decrypt_button.setDisabled(True)
            if self.__item.get_saved_obj().get_metadata()["note_id"] != -1:
                self.remove_note_button.setEnabled(True)
                self.add_note_button.setDisabled(True)
                self.get_note_button.setEnabled(True)
            else:
                self.remove_note_button.setDisabled(True)
                self.add_note_button.setEnabled(True)
                self.get_note_button.setDisabled(True)
        elif isinstance(self.__item.get_saved_obj(), Directory):
            self.encrypt_button.setDisabled(True)
            self.decrypt_button.setDisabled(True)
            self.remove_note_button.setDisabled(True)
            self.add_note_button.setDisabled(True)
            self.get_note_button.setDisabled(True)

    def __fullfill_list(self):
        """Fullfills the list of the view file window, and updates the buttons accordingly
        """
        self.list_widget.clear()
        if self.__item.get_in_vault_location():
            self.list_widget.addItem(QListWidgetItem(f"Location: {self.__item.get_in_vault_location()}"))
        for key, value in self.__item.get_saved_obj().get_metadata().items():
            if key == "last_modified" or key == "data_created":
                element = QListWidgetItem(f"{key}: {parse_timestamp_to_string(value)}")
            elif key == "icon_data_start" or key == "icon_data_end":
                continue
            else:
                element = QListWidgetItem(f"{key}: {value}")
            self.list_widget.addItem(element)
        if isinstance(self.__item.get_saved_obj(), File):
            self.__encrypted = self.__item.get_saved_obj().get_file_encrypted()
            self.list_widget.addItem(QListWidgetItem(f"file_encrypted: {self.__encrypted}"))
        self.__update_buttons()

    def __encrypt_or_decrypt_file(self, encrypt : bool):
        """Function to either encrypt or decrypt

        Args:
            encrypt (bool): True if to Encrypt, False to Decrypt
        """

        self.__dialog.password_string_label.setText(f'{"Encrypt:" if encrypt else "Decrypt:"} {self.__item.get_saved_obj().get_metadata()["name"]}.{self.__item.get_saved_obj().get_metadata()["type"]}')
        self.__dialog.exec()
        if self.__dialog.get_command() == "Skip":
            self.__dialog.reset_inner_items()
            return

        if encrypt:
            res = is_password_strong(self.__dialog.get_data())
            if not res[0]:
                msg = ''.join([f'- {reason}\n' for reason in res[1]])
                self.parent().show_message("Weak Password", msg, "Information", self)
                self.__dialog.reset_inner_items()
                return
            self.__encrypted = True
            self.encrypt_button.setDisabled(True)
            self.decrypt_button.setEnabled(True)
        else:
            self.__encrypted = False
            self.encrypt_button.setEnabled(True)
            self.decrypt_button.setDisabled(True)

        self.mythread = CustomThread(240 , self.__encrypt_or_decrypt_file.__name__)
        self.threads.append(self.mythread)

        self.worker = Worker(self.__process_file, self.parent().request_vault_path(), self.__item.get_saved_obj().get_loc_start(),
                             self.__item.get_saved_obj().get_loc_end(), self.__dialog.get_data(), self.__encrypted)
        self.worker.args += (self.worker.progress, )    # Force add signal

        self.worker.progress.connect(self.update_progress_bar)
        self.worker.moveToThread(self.mythread)
        self.mythread.started.connect(self.worker.run)

        def __end_worker_activity(emitted_result):
            self.mythread.stop_timer(emit_finish=False, emitted_result=emitted_result)
            self.worker.deleteLater()
        self.worker.finished.connect(__end_worker_activity)

        def __end_thread_activity(emitted_result):
            if isinstance (emitted_result, list):
                if emitted_result[0]:
                    old_end_loc = self.__item.get_saved_obj().get_loc_end()
                    direction = True
                    at_index = self.__item.get_saved_obj().get_loc_start() +1 # To account for ICONs
                    self.__item.get_saved_obj().set_file_encrypted(self.__encrypted)
                    self.__item.get_saved_obj().set_loc_end(emitted_result[2])
                    self.item_updated = True

                    self.parent().update_item_location(self.__item.get_saved_obj().get_id(), self.__item.get_saved_obj().get_loc_start(),
                                                       self.__item.get_saved_obj().get_loc_end(), "F")
                    if old_end_loc < self.__item.get_saved_obj().get_loc_end():
                        self.parent().request_data_shift(self.__item.get_saved_obj().get_loc_end() - old_end_loc, direction, at_index)
                    self.parent().update_file_data_in_vault(self.__item.get_saved_obj())
                else:
                    self.__encrypted = not self.__encrypted

                self.__dialog.reset_inner_items()
                self.__fullfill_list()

            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            self.mythread.quit()

        self.mythread.timeout_signal.connect(__end_thread_activity)
        self.mythread.finished.connect(self.mythread.deleteLater)

        self.progress_bar.setVisible(True)
        self.mythread.start()


    def __process_file(self, vault_path : str, file_start_loc : int, file_end_loc : int, password : str, encrypt: bool, progress_signal : pyqtSignal) -> list:
        """Process the encryption or decryption of the file

        Args:
            vault_path (str): The location of the vault
            file_start_loc (int): The starting index of the file in the vault
            file_end_loc (int): The ending index of the file in the vault
            password (str): The password to encrypt or decrypt with
            encrypt (bool): To define whether to encrypt or decrypt
            progress_signal (pyqtSignal): signal to update the progress bar

        Returns:
            list: First index is boolean value whether its successful or not, second is error if yes,
            third is new ending loc index, fourth is old ending loc index
        """
        the_file = get_file_from_vault(vault_path, file_start_loc, file_end_loc)

        progress_signal.emit(33)
        if encrypt:
            try:
                the_file = encrypt_bytes(the_file, password)
            except Exception as e:
                self.parent().show_message("Encryption Failure", e.message, "Error", self)
                return [False, e.message, file_end_loc, file_end_loc]
        else:
            try:
                the_file = decrypt_bytes(the_file, password)
            except Exception as e:
                self.parent().show_message("Decryption Failure", e.message, "Error", self)
                return [False, e.message, file_end_loc, file_end_loc]
        progress_signal.emit(33)

        old_size = file_end_loc-file_start_loc
        new_size = len(the_file)
        new_file_end_loc = file_start_loc + new_size
        byte_loss = new_size - old_size

        fd = None
        # Bigger means overwrite and shift
        if byte_loss > 0:
            fd = override_bytes_in_file(vault_path, the_file, byte_loss, at_location=file_start_loc)
        else:
            fd = override_bytes_in_file(vault_path, the_file, 0, at_location=file_start_loc)
        if fd:
            fd.close()

        res = [True, "", new_file_end_loc, file_end_loc]
        progress_signal.emit(100)
        return res

    def __add_note(self):
        """Adds a note to the file.
        """
        avd = NoteDialog(self.__item.get_saved_obj().get_id(),parent=self.parent())
        avd.exec()
        avd.close()
        avd.deleteLater()
        avd.destroy(True,True)
        avd = None
        self.__fullfill_list()

    def __get_note(self):
        """Gets the note note of the file
        """
        avd = NoteDialog(self.__item.get_saved_obj().get_metadata()["note_id"],add_note=False,parent=self.parent())
        avd.exec()
        avd.close()
        avd.deleteLater()
        avd.destroy(True,True)
        avd = None
        self.__fullfill_list()

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
        print("ViewFileWindow: Signaled for destruction")
        self.__dialog.reset_inner_items()
        self.__dialog.close()
        self.__dialog.deleteLater()
        self.exit()
        if self.item_updated:
            self.signal_for_destruction.emit(["Destroy",self.__item.get_saved_obj()])
        else:
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
