from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal

from utils.constants import ICON_1, ICON_2, ICON_3, ICON_6, MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT
from utils.extractors import get_files_and_folders_paths, get_item_info, get_amount_of_files_or_folders
from custom_exceptions.classes_exceptions import FileError, EncryptionFailure

from crypto.encryptors import get_file_and_encrypt_and_add_to_vault
from crypto.utils import get_checksum

from gui import VaultView
from gui.custom_widgets.custom_tree_widget import CustomTreeWidget
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_dropdown import CustomDropdown
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.custom_widgets.custom_messagebox import CustomMessageBox

from gui.threads.custom_thread import Worker, CustomThread
from gui.threads.mutable_boolean import MutableBoolean
from gui.threads.mutable_integer import MutableInteger
from math import floor

import os

# Can be used for both files and folders.
class AddFileWindow(QMainWindow):

    signal_for_destruction = pyqtSignal(str)

    def __init__(self, TheVaultView : VaultView):
        super().__init__(parent=TheVaultView)

        # Pointer to VaultView is parent
        self.setFocus()

        # Data
        self.threads = []
        self.__import_is_running = MutableBoolean(False)  # Can be requested to cancel operation
        self.__signaled_for_destruction = False
        # Window Data
        self.setObjectName("AddFileWindow")
        self.setWindowTitle("Add Content")
        self.setWindowIcon(QIcon(ICON_6))
        self.setMinimumWidth(MINIMUM_WINDOW_WIDTH)
        self.setMinimumHeight(MINIMUM_WINDOW_HEIGHT)
        self.resize(800, 600)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Vertical Layout is going to represent everything
        self.vertical_div = QVBoxLayout(self.centralwidget)

        # Tree Widget upper horziontal layout (Address bar, Insert button, Drive choice)
        current_address = os.getcwd().replace("\\","/")
        self.upper_horziontal_layout = QHBoxLayout()     # UpperVerticalLayout1 + UpperVerticalLayout2
        self.upper_vertical_layout1 = QVBoxLayout()      # (Address + Amount of Content)
        self.upper_vertical_layout2 = QVBoxLayout()      # (Insert Button + Drive)

        # Address -> upper_vertical_layout1
        self.address_bar = CustomLine(text=current_address,place_holder_text="Address path, e.g, C:\\Program Files",parent=self.centralwidget)
        self.address_bar.returnPressed.connect(lambda : self.on_insert_button_clicked(self.address_bar.text()))
        self.upper_vertical_layout1.addWidget(self.address_bar)

        # Amount of Content -> upper_vertical_layout1
        self.amount_of_content = CustomLine(text="", place_holder_text="Selected 0 Folders and 0 Files" ,parent=self.centralwidget)
        self.amount_of_content.setReadOnly(True)
        self.upper_vertical_layout1.addWidget(self.amount_of_content)

        # (Insert Button + Drive) = upper_vertical_layout2
        self.address_bar_button = CustomButton("Insert", QIcon(ICON_2), "Confirm the path to navigate", self.centralwidget)
        self.address_bar_button.set_action(lambda : self.on_insert_button_clicked(self.address_bar.text()))
        self.drive_dropdown = CustomDropdown(self.centralwidget) # OnCurrentIndexChanged will have a function call to repopulate the tree.
        self.upper_vertical_layout2.addWidget(self.address_bar_button)
        self.upper_vertical_layout2.addWidget(self.drive_dropdown)

        # Tree widget -> vertical_div
        self.tree_widget = CustomTreeWidget(parent=self.centralwidget, vaultview=False, vaultpath=None, header_map=None)
        self.tree_widget.populate(current_address)
        self.tree_widget.updated_signal.connect(self.address_bar.setText)
        self.tree_widget.marquee_signal.connect(self.modify_amount_of_content)

        def drive_dropdown_modify_location():
            drive = self.drive_dropdown.currentText()
            self.tree_widget.clear()
            self.tree_widget.populate(drive)
            self.address_bar.setText(drive)
        self.drive_dropdown.currentIndexChanged.connect(lambda: drive_dropdown_modify_location())

        # Merge Upper Layout with middle Part
        self.upper_horziontal_layout.addLayout(self.upper_vertical_layout1)
        self.upper_horziontal_layout.addLayout(self.upper_vertical_layout2)

        self.vertical_div.addLayout(self.upper_horziontal_layout)
        self.vertical_div.addWidget(self.tree_widget)

        # Bottom Part of the vault
        self.bottom_vertical_layout = QVBoxLayout()        # (Reset Button , Where In Vault) , {(Import Button)} , (Return Button , Add Bar)
        self.bottom_horziontal_sub_layout1 = QHBoxLayout() # (Reset Button , Where In Vault)
        self.bottom_horziontal_sub_layout2 = QHBoxLayout() # (Return Button , Add Bar)
        self.bottom_horziontal_sub_layout3 = QHBoxLayout() # (Import Button)

        # Reset Button , Where In Vault
        self.reset_fields_button = CustomButton("Reset", QIcon(ICON_3), "Reset all fields", self.centralwidget)
        self.reset_fields_button.clicked.connect(self.on_reset_button_clicked)
        self.where_in_vault = CustomLine(text="", place_holder_text="Where In Vault, e.g: / or /path/to",parent=self.centralwidget)
        self.bottom_horziontal_sub_layout1.addWidget(self.reset_fields_button)
        self.bottom_horziontal_sub_layout1.addWidget(self.where_in_vault)

        # Return button and Progress Bar
        self.return_button = CustomButton("Return", QIcon(ICON_1), "Return to VaultView", self)
        self.return_button.set_action(self.__open_vault_view)
        self.add_progress_bar = CustomProgressBar(parent=self.centralwidget)
        self.bottom_horziontal_sub_layout2.addWidget(self.return_button)
        self.bottom_horziontal_sub_layout2.addWidget(self.add_progress_bar)

        # Import butoon
        self.import_button = CustomButton("Import", QIcon(ICON_1), "Import Selected Items", self)
        self.import_button.set_action(self.__import_items)
        self.bottom_horziontal_sub_layout3.addWidget(self.import_button)

        # Merge Bottom into main
        self.bottom_vertical_layout.addLayout(self.bottom_horziontal_sub_layout1)
        self.bottom_vertical_layout.addLayout(self.bottom_horziontal_sub_layout2)
        self.bottom_vertical_layout.addLayout(self.bottom_horziontal_sub_layout3)
        self.vertical_div.addLayout(self.bottom_vertical_layout)

        # Additional information labels can be added here
        self.setCentralWidget(self.centralwidget)

    # Button insert handle results
    def on_insert_button_clicked(self, path : str) -> None:
        """If there is path added by the user, then update the tree view with it

        Args:
            path (str): Path given by the user
        """
        if not path:
            return
        self.address_bar.setText(path)
        drive = path[0] + ":\\" # Edge case when drive is only selected, first letter is taken
        for i in range(self.drive_dropdown.count()):
            if drive == self.drive_dropdown.itemText(i):
                self.drive_dropdown.setCurrentIndex(i)
                break
        self.tree_widget.clear()
        self.tree_widget.populate(path)

    # Button reset handle results
    def on_reset_button_clicked(self) -> None:
        """Reset all fields visible on the Window to empty strings. Also resets the TreeView
        """
        current_drive = self.drive_dropdown.currentText()
        self.address_bar.setText(current_drive)
        self.amount_of_content.setText("")
        self.where_in_vault.setText("/")
        self.tree_widget.clear()
        self.tree_widget.populate(current_drive)
        self.__clean_import()

    def modify_amount_of_content(self) -> None:
        """Function call when the tree widget marquee selection action is stopped
        """
        selected_items = self.tree_widget.getSelectedItems()
        if len (selected_items) == 0:
            self.amount_of_content.setText("")
            return None
        folders = 0
        files = 0
        for item in selected_items:
            if item.text(1) == "Folder":
                folders += 1
            else:
                files += 1
        text = f"Selected {folders} Folder{'s' if folders > 1 else ''} and {files} File{'s' if files > 1 else ''}"
        self.amount_of_content.setText(text)

    def __open_vault_view(self) -> None:
        """Returns back to the vault view sending a prompt to the vault view to destroy the window.
        """
        self.parent().show()
        self.parent().setFocus()
        print("Return back to vault view")
        self.exit()

    def __import_items(self) -> None:
        """Imports the selected items to the vault with a seperate thread. Contains the "ABORT" Mechanism
        """
        # Abort
        if self.import_button.text() == "Abort":
            self.__initiate_abort()
            return None

        # Check if path for Vault is valid
        path_vault = self.where_in_vault.text()
        is_path_ok = self.parent().on_insert_button_clicked(path=path_vault, check_location_only=True)   # Will show a message box
        if type(is_path_ok) == bool and not is_path_ok: # spaghetti
            return None
        insert_into = is_path_ok[1]

        # Check recursion limit
        if len(self.tree_widget.getSelectedItems()) == 0:
            message_box = CustomMessageBox(title="Nothing Selected", message="You need to select some items.",icon_box=QMessageBox.Icon.Warning, parent=self)
            message_box.show()
            return None

        selected_items = []
        file_total = 0
        folder_total = 0
        for item in self.tree_widget.getSelectedItems():
            if item.text(1) == "Folder":
                # The actual folder itself
                folder_total+=1
                # Amount of folders and files inside the given folder without subfolders (they are done every iteration)
                files, folders = get_amount_of_files_or_folders(item.get_path(), subfolders=False, include_files=True, include_folders=True)
                folder_total += folders
                file_total += files
                if folder_total > 100:
                    msg = f"Amount of folders including subfolders: {folder_total}, Next path's subfolders: {item.get_path()} will make it too much to add. Max is 100. Choose less!"
                    message_box = CustomMessageBox(title="Too Many", message=msg,icon_box=QMessageBox.Icon.Critical, parent=self)
                    message_box.show()
                    return None
            selected_items.append((item.text(1),item.get_path()))

        # Start import
        self.__lock_or_unlock_all(True)
        self.__import_is_running.set_value(True)

        self.mythread = CustomThread(allowed_runtime=100,function_name_to_handle="import_items")
        self.threads.append(self.mythread)
        self.worker = Worker(self.__process_import, selected_items, self.__import_is_running, folder_total, id_to_insert_into=insert_into)
        self.worker.args += (self.worker.progress, )    # Force add a signal progress

        self.worker.progress.connect(self.update_add_progress)
        self.worker.moveToThread(self.mythread)
        self.mythread.started.connect(self.worker.run)

        def __end_worker_activity(emitted_result):
            self.mythread.stop_timer(emit_finish=False, emitted_result=emitted_result)
            if not self.__import_is_running.get_value(): # Caused by Abort
                self.__import_is_running.set_value(True) # Will be turned by the following function
                if insert_into == self.tree_widget.current_path:
                    self.__update_header(refresh_tree=True)
                else:
                    self.__update_header(refresh_tree=False)
            self.worker.deleteLater()
        self.worker.finished.connect(__end_worker_activity)

        def __end_thread_activity():
            self.__update_header(refresh_tree=False)  # After import, the vault must have saved information.
            self.__clean_import()
            self.mythread.quit()
        self.mythread.timeout_signal.connect(__end_thread_activity)
        self.mythread.finished.connect(self.mythread.deleteLater)

        self.import_button.setText("Abort")
        self.import_button.button_label = "Abort"
        self.import_button.context_box_text = "Abort Operation Of Import"
        self.mythread.start()

    def __lock_or_unlock_all(self , lock : bool) -> None:
        """Function to lock or unlock all interactable items

        Args:
            lock (bool): True if lock , False if Unlock
        """
        if lock:
            self.tree_widget.selectionModel().clearSelection()
        self.address_bar.setReadOnly(lock)
        self.address_bar_button.setDisabled(lock)
        self.drive_dropdown.setDisabled(lock)
        self.tree_widget.setDisabled(lock)
        self.where_in_vault.setReadOnly(lock)
        self.reset_fields_button.setDisabled(lock)
        self.return_button.setDisabled(lock)

    def closeEvent(self, event):
        """Override for close window incase import is running.
        """
        if self.__import_is_running.get_value():
            event.ignore()
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Import is running")
            message_box.showMessage("Items are being imported, cannot close this right now. Please cancel operation if needed.")
        else:
            if not self.__signaled_for_destruction:
                self.exit()
            super().closeEvent(event)

    def __clean_import(self) -> None:
        """Cleans the widgets modified after the import operation
        """
        print("CLEAN")
        self.add_progress_bar.resetFormat()
        self.add_progress_bar.stop_progress(False)
        self.__import_is_running.set_value(False)
        self.__lock_or_unlock_all(False)
        self.import_button.setDisabled(False)
        self.import_button.setText("Import")
        self.import_button.button_label = "Import"
        self.import_button.context_box_text = "Import Selected Items"

    def __update_header(self, refresh_tree : bool = True) -> None:
        """Refreshes the header, and modifies the vault itself.

        Args:
            refresh_tree (bool, optional): Boolean to indicate whether to update the tree view. Defaults to True.
        """
        if self.__import_is_running.get_value():
            self.__import_is_running.set_value(False) # BruteForce
            self.parent().request_header_refresh(refresh_tree)

    def update_add_progress(self, num_to_update_with : int) -> None:
        """Updates the progress bar with the given value

        Args:
            emitted_num (int): Num to add into bar
        """
        if num_to_update_with == 100 or self.add_progress_bar.value() >= 100:
            self.add_progress_bar.stop_progress(False)
            return
        current_value = self.add_progress_bar.value()
        if num_to_update_with + current_value >= 100:
            self.add_progress_bar.setValue(99)
        else:
            self.add_progress_bar.setValue(num_to_update_with + current_value)

    def __process_import(self, selected_items : list[tuple[str,str]],
                         continue_running : MutableBoolean, recursions : int, signal : pyqtSignal,
                         call_num : MutableInteger = MutableInteger(0), id_to_insert_into : int = 0):
        """Function to perform the actual import of the items in the list

        Args:
            selected_items (list)[tuple[str,str]]: The list of Items to import, first tuple part is File/Folder, second is path
            continue_running (MutableBoolean): The mutuable boolean to abort operation
            recursions (int): An integer showing the number of expected recursions
            signal (pyqtSignal): A signal used to update the progress bar
            call_num (MutableInteger): A mutable integer showing the current recursion number
            id_to_insert_into(int): The ID of the directory to insert into

        """
        # Handle ID REMOVAL INCASE OF ABORT
        if not continue_running.get_value():
            self.parent().remove_folder_without_files(id_to_insert_into) # This id valid, since in the next recursion abort may be turned on.
            return None

        # Progress bar details
        progress_increase = 0
        if recursions < 1:
            progress_increase = 100
        else:
            progress_increase = floor(100 / recursions)

        amount_of_files = 0
        # Go through dirs:
        for folder in selected_items:
            if continue_running.get_value() and folder[0] == "Folder":
                v = call_num.get_value() + 1
                call_num.set_value(v)
                new_id_to_insert_into = 0
                res = get_item_info(folder[1])
                res["id"] = self.parent().request_new_id("D")
                res["path"] = id_to_insert_into
                new_id_to_insert_into = res["id"]
                self.parent().insert_item_into_vault(res, "D")
                self.__process_import(get_files_and_folders_paths(folder[1]), continue_running,
                                      recursions, signal, call_num=call_num, id_to_insert_into=new_id_to_insert_into)
            else:
                amount_of_files += 1

        # This is to make the progress bar accurate.
        to_emit = cntr = 0
        if amount_of_files == 0:
            to_emit = progress_increase
        else:
            to_emit = floor(progress_increase/amount_of_files)

        # Go through files
        for file in selected_items:

            if not continue_running.get_value():
                return None

            if file[0] != "Folder":

                lst = None
                try:
                    # lst will either return: [] , [int,int,int] , [int,int,int,int,int]
                    lst = get_file_and_encrypt_and_add_to_vault(self.parent().request_vault_password(), file[1],
                                                                self.parent().request_vault_path(), continue_running)
                except (FileError, EncryptionFailure) as e:
                    err = f'Couldnt add: {file[1]} because of error: {e}'
                    self.parent().logger.error(err)
                    continue

                res = get_item_info(file[1])
                if len(lst) < 3:   # No add and encrypt because continue running is false.
                    self.parent().logger.warn(f"Couldn't add {file[1]} because operation was cancelled")
                    continue
                if len(lst) > 3:
                    res["id"] = self.parent().request_new_id("F")
                    res["loc_start"] = lst[0]
                    res["loc_end"] = lst[1]
                    res["size"] = lst[2]
                    res["metadata"]["icon_data_start"] = -1
                    res["metadata"]["icon_data_end"] = -1
                    res["checksum"] = get_checksum(file[1])
                    res["path"] = id_to_insert_into
                else:
                    self.parent().logger.error(f"Couldn't add {file[1]} because list values {lst} are incomplete.")
                    continue
                if len(lst) == 4:
                    self.parent().logger.error(f"Couldn't add {file[1]} icon because {lst[3]}")
                elif len(lst) == 5:
                    res["metadata"]["icon_data_start"] = lst[3]
                    res["metadata"]["icon_data_end"] = lst[4]

                self.parent().insert_item_into_vault(res, "F")
                self.parent().request_file_id_addition_into_folder(id_to_insert_into,res["id"])
                self.parent().logger.info(f"Inserted {file[1]} into the vault")
                if cntr < progress_increase:
                    cntr+=to_emit
                    signal.emit(to_emit)
        if progress_increase > cntr:
            signal.emit(progress_increase-cntr)
        return None

    def __initiate_abort(self) -> None:
        """Start the abortion of the import process
        """
        self.__import_is_running.set_value(False)
        self.__lock_or_unlock_all(True)
        self.import_button.setDisabled(True)
        self.add_progress_bar.setFormat("Stopping..")

    def exit(self) -> None:
        """Cleans up any available threads and tries to close them along with the window.
        """
        self.clearFocus()
        self.__import_is_running.set_value(False)
        self.__signaled_for_destruction = True
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.hide()
        self.signal_for_destruction.emit("Destroy")
        self.close()
