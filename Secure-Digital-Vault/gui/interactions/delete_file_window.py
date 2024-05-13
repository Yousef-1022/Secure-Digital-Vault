from PyQt6.QtWidgets import QVBoxLayout, QMainWindow, QWidget, QListWidget, QListWidgetItem, QHBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon

from classes.directory import Directory
from classes.file import File

from file_handle.file_io import delete_bytes_from_file, get_file_size
from math import floor, ceil

from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.custom_widgets.custom_messagebox import CustomMessageBox
from gui.threads.custom_thread import CustomThread, Worker
from gui.threads.mutable_boolean import MutableBoolean
from gui.threads.mutable_integer import MutableInteger
from gui import VaultView

from utils.helpers import is_location_ok
from utils.constants import ICON_1


# Can be used for both files and folders.
class DeleteFileWindow(QMainWindow):

    signal_for_destruction = pyqtSignal(str)

    def __init__(self, parent : VaultView, items : list[CustomQTreeWidgetItem]):
        super().__init__(parent)
        self.setWindowTitle("Delete Items")
        self.setMinimumSize(600, 400)
        self.items = items

        # Custom Data
        self.threads = []
        self.__vault_loc = self.parent().request_vault_path()
        self.__delete_is_running = MutableBoolean(False)  # Can be requested to cancel operation
        self.__signaled_for_destruction = False

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
        self.delete_button = CustomButton("DELETE",QIcon(ICON_1), "Delete the items from the vault", self.central_widget)
        self.delete_button.set_action(self.on_delete_button_clicked)

        self.return_button = CustomButton("Return", QIcon(ICON_1), "Return to VaultView", self)
        self.return_button.set_action(self.__open_vault_view)

        # Progress report
        self.delete_progress_bar = CustomProgressBar(is_visible_at_start=False, parent=self.central_widget)

        # Merge layouts
        self.vertical_layout.addWidget(self.list_widget)
        self.horizontal_layout.addWidget(self.return_button)
        self.horizontal_layout.addWidget(self.delete_button)
        self.vertical_layout.addLayout(self.horizontal_layout)
        self.vertical_layout.addWidget(self.delete_progress_bar)

        # Additional information labels can be added here
        self.setCentralWidget(self.central_widget)

    def on_delete_button_clicked(self):
        """When the delete button is pressed, delete the items from the vault
        """

        if self.delete_button.text() == "ABORT":
            self.__initiate_abort()
            return None

        res = is_location_ok(location_path=self.__vault_loc, for_file_save=False, for_file_update=True)
        if not res[0]:
            window_title = "Location Problem"
            message = f"Could not delete anything from the {self.__vault_loc} on the system. Reason: {res[1]}"
            self.parent().show_message(window_title=window_title, message=message, parent=self)
            return

        # Mutuable data necessary for __process_delete
        lst = self.get_objects_from_list_view()
        cur_path = lst[0].get_path() if len(lst) > 0 else 0
        total_files = MutableInteger(0)
        for obj in lst:
            if isinstance(obj, Directory):
                tmp = total_files.get_value()
                total_files.set_value(len(obj.get_files()) + tmp)
            elif isinstance(obj, File):
                tmp = total_files.get_value()
                total_files.set_value(1 + tmp)
        removed_files = []
        total_deleted_bytes = MutableInteger(0)

        # Threading
        self.mythread = CustomThread(240 , self.on_delete_button_clicked.__name__)
        self.threads.append(self.mythread)


        self.worker = Worker(self.__process_delete, lst, self.__vault_loc, cur_path, total_files, removed_files,
                             total_deleted_bytes, self.__delete_is_running)
        self.worker.args += (self.worker.progress, )

        self.worker.progress.connect(self.update_delete_progress)
        self.worker.moveToThread(self.mythread)
        self.mythread.started.connect(self.worker.run)

        def __end_worker_activity(emitted_result):
            self.mythread.stop_timer(emit_finish=False, emitted_result=emitted_result)
            self.parent().update_vault_file_size((-1*total_deleted_bytes.get_value()))
            if not self.__delete_is_running.get_value(): # Caused by Abort
                self.__delete_is_running.set_value(True) # Will be turned off by the following function
                self.__update_header(refresh_tree=True)
            self.worker.deleteLater()
        self.worker.finished.connect(__end_worker_activity)

        def __end_thread_activity():
            self.delete_progress_bar.stop_progress()
            self.__update_header(refresh_tree=False)
            self.__clean_delete()
            self.mythread.quit()
        self.mythread.timeout_signal.connect(__end_thread_activity)
        self.mythread.finished.connect(self.mythread.deleteLater)

        self.delete_progress_bar.setVisible(True)
        self.delete_button.setText("ABORT")
        self.return_button.setDisabled(True)
        self.__delete_is_running.set_value(True)
        self.mythread.start()

    def update_delete_progress(self, num_to_update_with : int) -> None:
        """Updates the delete progress bar with the given value

        Args:
            emitted_num (int): Num to add into bar
        """
        if num_to_update_with == 100 or self.delete_progress_bar.value() >= 100:
            self.delete_progress_bar.stop_progress(False)
            return
        current_value = self.delete_progress_bar.value()
        if num_to_update_with + current_value >= 100:
            self.delete_progress_bar.setValue(99)
        else:
            self.delete_progress_bar.setValue(num_to_update_with + current_value)

    def __process_delete(self, items : list, vault_loc : str, cur_path : int, total_files : MutableInteger, removed_files : list[str],
                       total_deleted_bytes : MutableInteger, continue_running : MutableBoolean, signal : pyqtSignal, delete_cur_folder : bool = False):
        """Starts the delete process of the given items in the list

        Args:
            items (list): The items to delete, this lists consists of Files and Folders
            vault_loc (str): The location of the vault
            cur_path (int): The current path (Directory the items belong under)
            total_files (MutableInteger) : The TOTAL amount of files including the ones in the subfolders
            removed_files (list[str]) : The names of the removed files
            total_deleted_bytes (MutableInteger) : The TOTAL amount of deleted bytes
            continue_running (MutableBoolean): The mutuable boolean to abort operation
            signal (pyqtSignal): Signal to emit for the progress bar to increase
            delete_cur_folder (bool): Boolean to indicate whether to delete the current folder during the current iteration. ONLY USED BY RECURSION.
        """

        if not continue_running.get_value():
            return

        # Progress bar details
        if total_files.get_value() > 100:
            emit_every = floor(total_files.get_value() / 100)
        else:
            emit_every = ceil(100 / total_files.get_value())

        for obj in items:
            if not continue_running.get_value():
                return
            # Handle Directory
            if isinstance(obj , Directory):
                belong_to = obj.get_id()
                lst = self.parent().request_files_and_folders_from_vault(belong_to)
                self.__process_delete(items=lst, vault_loc=vault_loc, cur_path=belong_to, total_files=total_files,
                                      removed_files=removed_files, total_deleted_bytes=total_deleted_bytes,
                                      continue_running=continue_running, signal=signal, delete_cur_folder=True)
            # Handle File
            elif isinstance(obj, File):
                deleted_bytes = 0
                loc_file_start = obj.get_loc_start()
                loc_file_end   = obj.get_loc_end()
                loc_icon_start = obj.get_metadata()["icon_data_start"]
                loc_icon_end   = obj.get_metadata()["icon_data_end"]
                note_id  = obj.get_metadata()["note_id"]

                # Do everything in one file opening
                fd = open(vault_loc, "rb+")

                # 1: Delete Note
                if note_id != -1:
                    print(f"Deleting note {note_id}")
                    item = self.parent().get_item_class_from_vault(note_id,"V")
                    note_start = item.get_loc_start()
                    note_end   = item.get_loc_end()

                    init_size = get_file_size(vault_loc)
                    bytes_to_delete = note_end-note_start
                    o_index = note_start + bytes_to_delete
                    fd = delete_bytes_from_file(file_path=vault_loc, init_size=init_size, bytes_to_delete=bytes_to_delete,
                                           start_index=note_start, o_index=o_index, fd=fd)
                    deleted_bytes += bytes_to_delete
                    self.parent().request_data_shift(amount_to_shift = bytes_to_delete, direction = False, at_index = note_start)

                # 2: Delete Icon
                if loc_icon_start != -1 and loc_icon_end != -1:
                    print(f"Deleting icon {loc_icon_end} - {loc_icon_start} of {obj}")
                    init_size = get_file_size(vault_loc)
                    bytes_to_delete = loc_icon_end-loc_icon_start
                    o_index = loc_icon_start + bytes_to_delete
                    fd = delete_bytes_from_file(file_path=vault_loc, init_size=init_size, bytes_to_delete=bytes_to_delete,
                       start_index=loc_icon_start, o_index=o_index, fd=fd)
                    deleted_bytes += bytes_to_delete
                    self.parent().request_data_shift(amount_to_shift = bytes_to_delete, direction = False, at_index = loc_icon_start)

                # 3: Delete File
                init_size = get_file_size(vault_loc)
                bytes_to_delete = loc_file_end-loc_file_start
                o_index = loc_file_start + bytes_to_delete
                fd = delete_bytes_from_file(file_path=vault_loc, init_size=init_size, bytes_to_delete=bytes_to_delete,
                   start_index=loc_file_start, o_index=o_index, fd=fd)
                deleted_bytes += bytes_to_delete
                self.parent().request_data_shift(amount_to_shift = bytes_to_delete, direction = False, at_index = loc_file_start)

                # 4: Remove file from Vault and Folder
                fd.close()
                self.parent().remove_file_from_vault(obj.get_id())

                # 5: Update signal, removed_files, total_files, amount of deleted_bytes
                signal.emit(emit_every)
                file_name = f'{obj.get_metadata()["name"]}.{obj.get_metadata()["type"]}'
                removed_files.append(file_name)
                tmp = total_files.get_value()
                total_files.set_value(tmp-1)
                tmp = total_deleted_bytes.get_value()
                total_deleted_bytes.set_value(tmp+deleted_bytes)
                print(f"DELETED {file_name} from vault")

        # 6: The cur_path, which is the current folder does not have anything
        if delete_cur_folder:
            self.parent().remove_folder_without_files(cur_path)

    def get_objects_from_list_view(self) -> list:
        """Gets all the saved objects from the current list.

        Returns:
            list: List of Files or Directories
        """
        lst = []
        for object in self.items:
            lst.append(object.get_saved_obj())
        return lst

    def __open_vault_view(self) -> None:
        """Returns back to the vault view sending a prompt to the vault view to destroy the window.
        """
        self.parent().show()
        self.parent().setFocus()
        print("Return back to vault view")
        self.exit()

    def __initiate_abort(self) -> None:
        """Start the abortion of the delete process
        """
        self.__delete_is_running.set_value(False)
        self.delete_button.setDisabled(True)
        self.delete_progress_bar.setFormat("Stopping..")

    def __update_header(self, refresh_tree : bool = True) -> None:
        """Refreshes the header, and modifies the vault itself.

        Args:
            refresh_tree (bool, optional): Boolean to indicate whether to update the tree view. Defaults to True.
        """
        if self.__delete_is_running.get_value():
            self.__delete_is_running.set_value(False)
            self.parent().request_header_refresh(refresh_tree)

    def __clean_delete(self) -> None:
        """Cleans the widgets modified after the import operation
        """
        print("CLEAN")
        self.delete_progress_bar.resetFormat()
        self.delete_progress_bar.stop_progress(False)
        self.__delete_is_running.set_value(False)
        self.delete_button.setDisabled(False)
        self.delete_button.setText("DELETE")
        self.delete_button.button_label = "Delete"
        self.delete_button.context_box_text = "Delete Selected Items"
        self.return_button.setEnabled(True)

    def closeEvent(self, event):
        """Override for close window incase import is running.
        """
        if self.__delete_is_running.get_value():
            event.ignore()
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Delete is running")
            message_box.showMessage("Items are being Deleted, cannot close this right now. Please cancel operation if needed.")
        else:
            if not self.__signaled_for_destruction:
                self.exit()
            super().closeEvent(event)

    def exit(self):
        """Cleans up any available threads and tries to close them along with the window.
        """
        self.clearFocus()
        self.__delete_is_running.set_value(False)
        self.__signaled_for_destruction = True
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.hide()
        self.signal_for_destruction.emit("Destroy")
        self.close()
