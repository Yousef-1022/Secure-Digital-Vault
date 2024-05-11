from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, QMainWindow, QWidget
from PyQt6.QtGui import QIcon

from utils.constants import ICON_1, ICON_2, ICON_3, ICON_4, ICON_6, ICON_7
from utils.helpers import is_proper_extension
from logger.logging import Logger

from crypto.decryptors import decrypt_header
from custom_exceptions.utils_exceptions import MagicFailure
from custom_exceptions.classes_exceptions import DecryptionFailure

from gui import ViewManager
from gui.custom_widgets.custom_tree_widget import CustomTreeWidget
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_dropdown import CustomDropdown
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_messagebox import CustomMessageBox
from gui.custom_widgets.custom_line_password import CustomPasswordLineEdit
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.threads.custom_thread import Worker, CustomThread

import os


class VaultSearchWindow(QMainWindow):
    def __init__(self, VaultViewManager : ViewManager):
        super().__init__()

        # Pointer to ViewManager
        self.__view_manager = VaultViewManager
        # Window Data
        self.threads = []
        self.setObjectName("VaultSearchWindow")
        self.setWindowTitle("Vault Search Window")
        self.setWindowIcon(QIcon(ICON_6))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.resize(1024, 768)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Vertical Layout is going to represent everything
        self.vertical_div = QVBoxLayout(self.centralwidget)

        # Tree Widget upper horziontal layout (Address bar, Insert button, Drive choice)
        current_address = os.getcwd().replace("\\","/")
        self.upper_horziontal_layout = QHBoxLayout()     # UpperVerticalLayout1 + UpperVerticalLayout2
        self.upper_horziontal_sublayout = QHBoxLayout()  # (Extension , Detect Button)
        self.upper_vertical_layout1 = QVBoxLayout()      # Address , (Extension , Detect Button)
        self.upper_vertical_layout2 = QVBoxLayout()      # (Insert Button + Drive)

        # Address -> upper_vertical_layout1
        self.address_bar = CustomLine(text=current_address,place_holder_text="Address path, e.g, C:\Program Files",parent=self.centralwidget)
        self.address_bar.returnPressed.connect(lambda : self.on_insert_button_clicked(self.address_bar.text()))
        self.upper_vertical_layout1.addWidget(self.address_bar)

        # (Extension , Detect Button) = upper_horziontal_sublayout -> upper_vertical_layout1
        self.vault_extension_line = CustomLine(text="", place_holder_text="Vault extension, e.g., .vault" ,parent=self.centralwidget)
        self.detect_vault_button = CustomButton("Detect", QIcon(ICON_1),
                                              "Detects vault in recently viewed directory and inserts it into vault location line",
                                              self.centralwidget)
        self.detect_vault_button.set_action(lambda : self.on_detect_button_clicked(self.vault_extension_line.text()))
        self.upper_horziontal_sublayout.addWidget(self.vault_extension_line)
        self.upper_horziontal_sublayout.addWidget(self.detect_vault_button)
        self.upper_vertical_layout1.addLayout(self.upper_horziontal_sublayout)

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

        def drive_dropdown_modify_location():
            drive = self.drive_dropdown.currentText()
            self.tree_widget.clear()
            self.tree_widget.populate(drive)
            self.address_bar.setText(drive)
        self.drive_dropdown.currentIndexChanged.connect(lambda: drive_dropdown_modify_location())

        # Merge Upper Layout with middle Part
        self.upper_horziontal_layout.addLayout(self.upper_vertical_layout1)
        self.upper_horziontal_layout.addLayout(self.upper_vertical_layout2)
        self.detect_vault_button_progress_bar = CustomProgressBar(is_visible_at_start=False, parent=self.centralwidget)

        self.vertical_div.addLayout(self.upper_horziontal_layout)
        self.vertical_div.addWidget(self.detect_vault_button_progress_bar)
        self.vertical_div.addWidget(self.tree_widget)

        # Bottom Part of the vault
        self.bottom_vertical_layout1 = QVBoxLayout()       # (Password , Reset Button) , (Vault Location , Import Button)
        self.bottom_horziontal_sub_layout1 = QHBoxLayout() # (Password , Reset Button)
        self.bottom_horziontal_sub_layout2 = QHBoxLayout() # (Vault Location , Import Button)
        self.bottom_horziontal_sub_layout3 = QHBoxLayout() # (Return Button , Decrypt Bar)

        # Password line edit , Reset Button
        self.password_line_edit = CustomPasswordLineEdit(placeholder_text="Vault password", icon=QIcon(ICON_7) , parent=self.centralwidget)
        self.reset_fields_button = CustomButton("Reset", QIcon(ICON_3), "Reset all fields", self.centralwidget)
        self.reset_fields_button.clicked.connect(self.on_reset_button_clicked)
        self.bottom_horziontal_sub_layout1.addWidget(self.reset_fields_button)
        self.bottom_horziontal_sub_layout1.addWidget(self.password_line_edit)

        # Vault Location line edit , Import Button
        self.vault_location_line = CustomLine(text="", place_holder_text="Vault location",parent=self.centralwidget)
        self.import_vault_button = CustomButton("Import", QIcon(ICON_4), "Click to import vault once the password and file location are filled",
                                              self.centralwidget)
        self.import_vault_button.set_action(self.on_import_button_clicked)
        self.bottom_horziontal_sub_layout2.addWidget(self.vault_location_line)
        self.bottom_horziontal_sub_layout2.addWidget(self.import_vault_button)

        def treeWidgetModifyLocationAndExtension(file_path : str) -> None:
            self.vault_location_line.setText(file_path)
            self.vault_extension_line.setText(file_path[file_path.rfind('.'):])
        self.tree_widget.clicked_file_signal.connect(treeWidgetModifyLocationAndExtension)

        # Return button and Progress Bar
        self.return_button = CustomButton("Return", QIcon(ICON_1), "Return to MainMenu", self)
        self.return_button.set_action(self.__open_view_manager)
        self.decrypt_progress_bar = CustomProgressBar(parent=self.centralwidget)
        self.bottom_horziontal_sub_layout3.addWidget(self.return_button)
        self.bottom_horziontal_sub_layout3.addWidget(self.decrypt_progress_bar)

        # Merge Bottom into main
        self.bottom_vertical_layout1.addLayout(self.bottom_horziontal_sub_layout1)
        self.bottom_vertical_layout1.addLayout(self.bottom_horziontal_sub_layout2)
        self.bottom_vertical_layout1.addLayout(self.bottom_horziontal_sub_layout3)
        self.vertical_div.addLayout(self.bottom_vertical_layout1)

        # Additional information labels can be added here
        self.setCentralWidget(self.centralwidget)

    # Button click handlers
    def detect_vault(self, vault_extension: str, cwd : str) -> str:
        """Searches for the vault in the given directory

        Args:
            vault_extension (str): Vault extension
            cwd (str): Current Working Directory

        Returns:
            str: Location of the vault, None if not available
        """
        if not is_proper_extension(vault_extension):
            return None
        if not cwd:
            current_directory = os.getcwd()
        else:
            current_directory = cwd
        for root, dirs, files in os.walk(current_directory):
            for file in files:
                if file.endswith(vault_extension):
                    modified_string = os.path.join(root, file).replace("\\", "/")
                    return modified_string
        return None

    # Button detect handle results
    def on_detect_button_clicked(self, vault_extension: str) -> None:
        """Attempts to find the given vault_extension in the displayed working dir with a seperate thread.
        Updates vault_location_line with `Not Found` or the vault location

        Args:
            vault_extension (str): vault_extension aka .vault
        """
        extension = vault_extension.replace(" ", "")
        if not is_proper_extension(extension):
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Vault extension")
            message_box.showMessage(f"The extension: '{extension}' of the vault is invalid!")
            return None
        for t in self.threads:
            if(t.handled_function == "detect_vault" and not t.timer_finished):
                self.logger.info(f"{t} is Already running with {t.handled_function}")
                return

        self.mythread = CustomThread(10 , self.detect_vault.__name__)
        self.threads.append(self.mythread)
        cwd = self.address_bar.text() if self.address_bar.text() is not None else self.drive_dropdown.currentText()
        self.worker = Worker(self.detect_vault, vault_extension, cwd)

        self.worker.moveToThread(self.mythread)
        self.mythread.started.connect(self.worker.run)

        def __end_worker_activity(emitted_result):
            self.mythread.stop_timer(emit_finish=False, emitted_result=emitted_result)
            self.worker.deleteLater()
        self.worker.finished.connect(__end_worker_activity)

        def update_detected_button_progress(emitted_num : int) -> None:
            if emitted_num == 100 or self.detect_vault_button_progress_bar.value() >= 100:
                self.detect_vault_button_progress_bar.stop_progress()
                self.detect_vault_button.setDisabled(False)
                return
            if self.detect_vault_button_progress_bar.value() == 0:
                self.detect_vault_button_progress_bar.setVisible(True)
            current_value = self.detect_vault_button_progress_bar.value()
            if emitted_num + current_value >= 100:
                self.detect_vault_button_progress_bar.setValue(99)
            else:
                self.detect_vault_button_progress_bar.setValue(emitted_num + current_value)

        self.mythread.progress.connect(update_detected_button_progress)

        def __end_thread_activity(emitted_obj):
            self.vault_location_line.setText(str(emitted_obj))
            self.detect_vault_button_progress_bar.stop_progress()
            self.mythread.quit()

        self.mythread.timeout_signal.connect(__end_thread_activity)
        self.mythread.finished.connect(self.mythread.deleteLater)

        self.detect_vault_button.setDisabled(True)
        self.mythread.start()

    # Button reset handle results
    def on_reset_button_clicked(self) -> None:
        """Reset all fields visible on the Window to empty strings. Also resets the TreeView
        """
        current_drive = self.drive_dropdown.currentText()
        self.address_bar.setText(current_drive)
        self.vault_extension_line.setText("")
        self.tree_widget.clear()
        self.tree_widget.populate(current_drive)
        self.password_line_edit.get_passwordLine().setText("")
        self.vault_location_line.setText("")

    # Button import handle results
    def on_import_button_clicked(self) -> None:
        """Logic to import vault
        """
        password = self.password_line_edit.get_passwordLine().text()
        vault_loc = self.vault_location_line.text()
        vault_extension = self.vault_extension_line.text().replace(" ", "")

        message_box = CustomMessageBox(parent=self)
        if not password:
            message_box.setIcon(QMessageBox.Icon.Critical)
            message_box.setWindowTitle("No Password")
            message_box.showMessage("Password field is empty!")
            return
        elif not vault_loc:
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Unknown vault location")
            message_box.showMessage("No vault location has been chosen!")
            return
        elif not is_proper_extension(vault_extension):
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Vault Extension")
            message_box.showMessage("The extension of the vault is not correct!")
            return
        elif not vault_extension == vault_loc[vault_loc.rfind('.'):]:
            message_box.setIcon(QMessageBox.Icon.Critical)
            message_box.setWindowTitle("Vault Extension")
            message_box.showMessage(f"The extension of the vault: '{vault_extension}' does not correspond to the extension of '{vault_loc}'!")
            return
        else:
            print(f"Password: {password} - Vault location: {vault_loc} - Extension: {vault_extension}. Redirect to vault view")
            #TODO: Add the password hint stuff

            # Seperate Thread
            self.mythread = CustomThread(20 , self.decrypt_given_vault.__name__)
            self.threads.append(self.mythread)

            self.worker = Worker(self.decrypt_given_vault, vault_loc, password)
            self.worker.moveToThread(self.mythread)
            self.mythread.started.connect(self.worker.run)

            def __end_worker_activity(emitted_result):
                self.mythread.stop_timer(emit_finish=False, emitted_result=emitted_result)
                self.worker.deleteLater()
            self.worker.finished.connect(__end_worker_activity)

            # Progress functions
            def update_decrypt_progress(emitted_num : int) -> None:
                if emitted_num == 100 or self.decrypt_progress_bar.value() >= 100:
                    self.decrypt_progress_bar.stop_progress(False)
                    self.import_vault_button.setDisabled(False)
                    return
                current_value = self.decrypt_progress_bar.value()
                if emitted_num + current_value >= 100:
                    self.decrypt_progress_bar.setValue(99)
                else:
                    self.decrypt_progress_bar.setValue(emitted_num + current_value)

            self.mythread.progress.connect(update_decrypt_progress)

            def __end_thread_activity():
                self.decrypt_progress_bar.stop_progress()
                self.mythread.quit()
            self.mythread.timeout_signal.connect(__end_thread_activity)
            self.mythread.finished.connect(self.mythread.deleteLater)

            self.import_vault_button.setDisabled(True)
            self.mythread.start()


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

    def decrypt_given_vault(self, vault_loc : str , password : str):
        try:
            actual_header = decrypt_header(vault_loc,password)
        except MagicFailure as e:
            self.__show_message("Corrupted Vault",Logger.form_log_message(e, "ERROR"), "Error")
            return
        except DecryptionFailure as e:
            self.__show_message("Decryption Failure", Logger.form_log_message(e), "Error")
            return # TODO hint
        self.__view_manager.set_special_h(actual_header)
        self.__view_manager.set_special_p(password)
        self.__view_manager.set_vault_pointer(vault_loc)
        self.__view_manager.signal_to_open_window.emit("VaultView")
        return

    def __open_view_manager(self):
        self.__view_manager.signal_to_open_window.emit("")

    def closeEvent(self, event):
        """Override for close window incase import is running.
        """
        if self.__view_manager:
            self.__view_manager.signal_to_open_window.emit("")
        self.exit()
        super().closeEvent(event)

    def __show_message(self, window_title : str, message : str, type : str = "Warning"):
        """Display a message box with the given details.

        Args:
            window_title(str): the title of the message
            message(str): the message itself
            type(str) optional: type of the icon to show
        """
        message_box = CustomMessageBox(parent=self)
        if type not in [enum.name for enum in QMessageBox.Icon]:
            message_box.setIcon(QMessageBox.Icon.Warning)
        else:
            message_box.setIcon(QMessageBox.Icon[type])
        message_box.setWindowTitle(window_title)
        message_box.showMessage(message)
        message_box.close()
        message_box.deleteLater()

    # Cleanup
    def exit(self) -> None:
        """Cleans up any available threads and tries to close them along with the window.
        """
        self.__view_manager = None
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.hide()
        self.close()
