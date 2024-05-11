from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QListWidget, QListWidgetItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal

from classes.file import File
from classes.directory import Directory

from gui.threads.custom_thread import Worker, CustomThread
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui.interactions.voice_dialog import VoiceDialog
from gui.interactions.interact_dialog import InteractDialog
from gui import VaultView

from utils.constants import ICON_1
from utils.parsers import parse_timestamp_to_string


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

        self.remove_voice_button = CustomButton("Remove VoiceNote", QIcon(ICON_1), "Remove voice note from file", self.central_widget)

        self.add_voice_button = CustomButton("Add VoiceNote", QIcon(ICON_1), "Add voice note to file", self.central_widget)
        self.add_voice_button.set_action(self.__add_voice_note)
        self.get_voice_button = CustomButton("Get VoiceNote", QIcon(ICON_1), "Get the VoiceNote", self.central_widget)
        self.get_voice_button.set_action(self.__get_voice_note)

        # List widget to display items
        self.list_widget = QListWidget(self)
        self.__fullfill_list()

        # Progress report
        self.progress_bar = CustomProgressBar(is_visible_at_start=False, parent=self.central_widget)

        # Add buttons to self.vertical_layout
        self.button_layout.addWidget(self.encrypt_button)
        self.button_layout.addWidget(self.decrypt_button)
        self.button_layout.addWidget(self.remove_voice_button)
        self.button_layout.addWidget(self.add_voice_button)
        self.button_layout.addWidget(self.get_voice_button)
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
            if self.__item.get_saved_obj().get_metadata()["voice_note_id"] != -1:
                self.remove_voice_button.setEnabled(True)
                self.add_voice_button.setDisabled(True)
                self.get_voice_button.setEnabled(True)
            else:
                self.remove_voice_button.setDisabled(True)
                self.add_voice_button.setEnabled(True)
                self.get_voice_button.setDisabled(True)
        elif isinstance(self.__item.get_saved_obj(), Directory):
            self.encrypt_button.setDisabled(True)
            self.decrypt_button.setDisabled(True)
            self.remove_voice_button.setDisabled(True)
            self.add_voice_button.setDisabled(True)
            self.get_voice_button.setDisabled(True)

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
            self.__encrypted = True
            self.encrypt_button.setDisabled(True)
            self.decrypt_button.setEnabled(True)
        else:
            self.__encrypted = False
            self.encrypt_button.setEnabled(True)
            self.decrypt_button.setDisabled(True)

        self.mythread = CustomThread(240 , self.__encrypt_or_decrypt_file.__name__)
        self.threads.append(self.mythread)

        self.worker = Worker(self.__process_file, self.__item.get_path(), self.__item.get_saved_obj().get_loc_start(),
                             self.__item.get_saved_obj().get_loc_end(), self.__dialog.get_data())
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
                    self.__item.get_saved_obj().set_file_encrypted(self.__encrypted)
                    self.__item.get_saved_obj().set_loc_end(emitted_result[2])
                    self.item_updated = True
                self.__dialog.reset_inner_items()
                self.__fullfill_list()
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            self.mythread.quit()
        self.mythread.timeout_signal.connect(__end_thread_activity)
        self.mythread.finished.connect(self.mythread.deleteLater)

        self.progress_bar.setVisible(True)
        self.mythread.start()


    def __process_file(self, vault_path : str, file_start_loc : int, file_end_loc : int, password : str, progress_signal : pyqtSignal) -> list:
        """Process the encryption or decryption of the file

        Args:
            vault_path (str): The location of the vault
            file_start_loc (int): The starting index of the file in the vault
            file_end_loc (int): The ending index of the file in the vault
            password (str): The password to encrypt with
            progress_signal (pyqtSignal): signal to update the progress bar

        Returns:
            list: First index is boolean value whether its successful or not, second is error if yes,
            third is new ending loc index, fourth is old ending loc index
        """
        # TODO:
        print(f"Please process {vault_path} from index {file_start_loc} with password: {password}")
        new_file_end_loc = file_end_loc
        res = [True, "", file_end_loc, new_file_end_loc]
        progress_signal.emit(1)
        import time
        time.sleep(0.3) #TODO: Remove this
        return res

    def __add_voice_note(self):
        """Adds a note to the file.
        """
        avd = VoiceDialog(self.__item.get_saved_obj().get_id(),parent=self.parent())
        avd.exec()
        avd.close()
        avd.deleteLater()
        avd.destroy(True,True)
        avd = None
        self.__fullfill_list()

    def __get_voice_note(self):
        """Gets the voice note of the file
        """
        avd = VoiceDialog(self.__item.get_saved_obj().get_metadata()["voice_note_id"],add_voice=False,parent=self.parent())
        avd.exec()
        avd.close()
        avd.deleteLater()
        avd.destroy(True,True)
        avd = None
        self.__fullfill_list()

    def update_progress_bar(self, num_to_update_with : int) -> None:
        """Updates the progress bar with the given value

        Args:
            emitted_num (int): _description_
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
        if self.item_updated:
            self.signal_for_destruction.emit(["Destroy",self.__item.get_saved_obj()])
        else:
            self.signal_for_destruction.emit("Destroy")
        self.exit()
        self.close()
        super().closeEvent(event)

    def exit(self):
        """Cleans up any available threads and tries to close them along with the window.
        """
        self.clearFocus()
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.hide()
