from PyQt6.QtWidgets import QVBoxLayout, QMainWindow, QWidget, QListWidget, QListWidgetItem, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, QDir
from PyQt6.QtGui import QIcon

from classes.directory import Directory
from classes.file import File

from file_handle.file_io import create_folder_on_disk, append_bytes_into_file
from math import floor, ceil

from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.threads.custom_thread import CustomThread, Worker
from gui.interactions.interact_dialog import InteractDialog
from gui import VaultView

from utils.helpers import get_available_drives, is_location_ok
from utils.constants import ICON_1
from utils.parsers import show_as_windows_directory
from utils.extractors import get_file_from_vault
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
        self.address_bar.returnPressed.connect(lambda : self.on_extract_button_clicked(self.address_bar.text()))
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
                full_path = self.parent().request_path_string(the_id = item.get_saved_obj().get_path(), full_path = False, type = "F")
                item.get_saved_obj().set_path(full_path)
                all_files.append(item.get_saved_obj())
            elif isinstance(item.get_saved_obj(), Directory):
                res = self.parent().request_files_from_vault(item.get_saved_obj().get_id(), False, item.get_saved_obj().get_name()) # Must get initial parent
                all_files.extend(res)
        dir_loc = show_as_windows_directory(path)

        # Threading
        self.mythread = CustomThread(240 , self.on_extract_button_clicked.__name__)
        self.worker = Worker(self.process_extract, all_files, dir_loc, self.__vault_loc, self.__vault_pass, self.__interactable)
        self.worker.args += (self.worker.interaction, )
        self.worker.args += (self.worker.progress, )    # Force add signals

        self.worker.interaction.connect(self.interaction_function)
        self.worker.progress.connect(self.update_extract_progress)
        self.worker.moveToThread(self.mythread)
        self.mythread.started.connect(self.worker.run)

        def __end_worker_activity(emitted_result):
            self.mythread.stop_timer(emit_finish=False, emitted_result=emitted_result)
            self.mythread.quit()
            self.worker.deleteLater()
        self.worker.finished.connect(__end_worker_activity)
        #self.worker.finished.connect(self.mythread.deleteLater) _ PLACEHOLDER TODO

        def __end_thread_activity():
            self.extraction_progress_bar.setValue(0)
            self.extraction_progress_bar.setVisible(False)
            self.address_bar.setEnabled(True)
            self.mythread.quit()
        self.mythread.timeout_signal.connect(__end_thread_activity)
        #self.mythread.finished.connect(self.mythread.deleteLater) _ PLACEHOLDER TODO

        self.extraction_progress_bar.setVisible(True)
        self.address_bar.setDisabled(True)
        self.mythread.start()

    def update_extract_progress(self, num_to_update_with : int) -> None:
        """Updates the extractin progress bar with the given value

        Args:
            emitted_num (int): _description_
        """
        if num_to_update_with == 100 or self.extraction_progress_bar.value() == 100:
            self.extraction_progress_bar.stop_progress(False)
            return
        current_value = self.extraction_progress_bar.value()
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

        for file in lst:
            password = None

            time.sleep(0.3) #TODO: Remove this

            # Check if file encrypted, open dialog:
            if file.get_file_encrypted():
                # Set interactable object data. 0 = KeepRunning (bool), 1 = RequestType (str), 2 = Name (str)
                interactable_item[0] = True         # Keep running
                interactable_item[1] = "Password"   # Request
                interactable_item[2] = file.get_path() + f'{file.get_metadata()["name"]}.{file.get_metadata()["type"]}'
                interaction_signal.emit(interactable_item)

                while interactable_item[0] == True:
                    time.sleep(1)   # Wait for response

                if interactable_item[1] == "Skip":
                    print(f"Skipping: {file.get_path()}{file.get_metadata()['name']}.{file.get_metadata()['type']}")
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
            print(f"Creating: {folder_location}{full_file_name}{' but has password '+password if password else ''}. VaultPass: {vault_password}")
            res = create_folder_on_disk(folder_location)
            if not res:
                self.parent().logger.log(f"Couldn't create location: {folder_location}")
                continue

            # TODO: 1:Better get, 2: Decrypt while get. If password is not None (For if Encrypted)
            file_from_vault = get_file_from_vault(vault_loc, file.get_loc_start(), file.get_loc_end())
            res = append_bytes_into_file(folder_location, file_from_vault, create_file=True, file_name=full_file_name)

            # TODO: Handle res result
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
        print("Extraction done")

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
        print("GetFileWindow: Signaled for destruction")
        self.__dialog.reset_inner_items()
        self.__dialog.close()
        self.__dialog.deleteLater()
        self.signal_for_destruction.emit("Destroy")
        super().closeEvent(event)
