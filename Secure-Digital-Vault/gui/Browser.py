from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, QMainWindow, QStatusBar, QWidget
from PyQt6.QtGui import QIcon

from utils.constants import ICON_1, ICON_2, ICON_3, ICON_4, ICON_6, ICON_7
from utils.validators import is_proper_extension
from logger.logging import Logger

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
    def __init__(self):
        super().__init__()

        # Window Data
        self.logger = Logger()
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
        currentAddress = os.getcwd().replace("\\","/")
        self.treeWidgetUpperHorziontalLayout = QHBoxLayout()
        self.treeWidgetUpperHorziontalSubLayout1 = QHBoxLayout() # (Extension , Detect Button)
        self.treeWidgetUpperVerticalLayout1 = QVBoxLayout()   # Address , (Extension , Detect Button)
        self.treeWidgetUpperVerticalLayout2 = QVBoxLayout()   # (Insert Button + Drive)

        # Address -> treeWidgetUpperVerticalLayout1
        self.treeWidgetAddressBar = CustomLine(self.centralwidget)
        self.treeWidgetAddressBar.setPlaceholderText("Address path, e.g, C:\Program Files")
        self.treeWidgetAddressBar.setText(currentAddress)
        self.treeWidgetAddressBar.returnPressed.connect(lambda : self.on_insert_button_clicked(self.treeWidgetAddressBar.text()))
        self.treeWidgetUpperVerticalLayout1.addWidget(self.treeWidgetAddressBar)

        # (Extension , Detect Button) = treeWidgetUpperHorziontalSubLayout1 -> treeWidgetUpperVerticalLayout1
        self.vaultExtensionLine = CustomLine(self.centralwidget)
        self.vaultExtensionLine.setPlaceholderText("Vault extension, e.g., .vault")
        self.detectVaultButton = CustomButton("Detect", QIcon(ICON_1),
                                              "Detects vault in recently viewed directory and inserts it into vault location line",
                                              self.centralwidget)
        self.detectVaultButton.set_action(lambda : self.on_detect_button_clicked(self.vaultExtensionLine.text()))
        self.treeWidgetUpperHorziontalSubLayout1.addWidget(self.vaultExtensionLine)
        self.treeWidgetUpperHorziontalSubLayout1.addWidget(self.detectVaultButton)
        self.treeWidgetUpperVerticalLayout1.addLayout(self.treeWidgetUpperHorziontalSubLayout1)

        # (Insert Button + Drive) = treeWidgetUpperVerticalLayout2
        self.treeWidgetAddressBarButton = CustomButton("Insert", QIcon(ICON_2), "Confirm the path to navigate", self.centralwidget)
        self.treeWidgetAddressBarButton.set_action(lambda : self.on_insert_button_clicked(self.treeWidgetAddressBar.text()))
        self.driveDropdown = CustomDropdown(self.centralwidget) # OnCurrentIndexChanged will have a function call to repopulate the tree.
        self.treeWidgetUpperVerticalLayout2.addWidget(self.treeWidgetAddressBarButton)
        self.treeWidgetUpperVerticalLayout2.addWidget(self.driveDropdown)

        # Tree widget -> vertical_div
        self.treeWidget = CustomTreeWidget(columns=4,vaultview=False, vaultpath=None, header_map=None, parent=self.centralwidget)
        self.treeWidget.populate(currentAddress)
        self.treeWidget.updated_signal.connect(self.treeWidgetAddressBar.setText)

        def driveDropdownModifyLocation():
            drive = self.driveDropdown.currentText()
            self.treeWidget.populate(drive)
            self.treeWidgetAddressBar.setText(drive)
        self.driveDropdown.currentIndexChanged.connect(lambda: driveDropdownModifyLocation())

        # Merge Upper Layout with middle Part
        self.treeWidgetUpperHorziontalLayout.addLayout(self.treeWidgetUpperVerticalLayout1)
        self.treeWidgetUpperHorziontalLayout.addLayout(self.treeWidgetUpperVerticalLayout2)
        self.detectVaultButtonProgressBar = CustomProgressBar(is_visible_at_start=False, parent=self.centralwidget)

        self.vertical_div.addLayout(self.treeWidgetUpperHorziontalLayout)
        self.vertical_div.addWidget(self.detectVaultButtonProgressBar)
        self.vertical_div.addWidget(self.treeWidget)

        # Bottom Part of the vault
        self.treeWidgetBottomVerticalLayout1 = QVBoxLayout() # (Password , Reset Button) , (Vault Location , Import Button)
        self.treeWidgetBottomHorziontalSubLayout1 = QHBoxLayout() # (Password , Reset Button)
        self.treeWidgetBottomHorziontalSubLayout2 = QHBoxLayout() # (Vault Location , Import Button)

        # Password line edit , Reset Button
        self.passwordLineEdit = CustomPasswordLineEdit(placeholder_text="Vault password", icon=QIcon(ICON_7) , parent=self.centralwidget)
        self.resetFieldsButton = CustomButton("Reset", QIcon(ICON_3), "Reset all fields", self.centralwidget)
        self.resetFieldsButton.clicked.connect(self.on_reset_button_clicked)
        self.treeWidgetBottomHorziontalSubLayout1.addWidget(self.resetFieldsButton)
        self.treeWidgetBottomHorziontalSubLayout1.addWidget(self.passwordLineEdit)

        # Vault Location line edit , Import Button
        self.vaultLocationLine = CustomLine(self.centralwidget)
        self.vaultLocationLine.setPlaceholderText("Vault location")
        self.importVaultButton = CustomButton("Import", QIcon(ICON_4), "Click to import vault once the password and file location are filled",
                                              self.centralwidget)
        self.importVaultButton.set_action(self.on_import_button_clicked)
        self.treeWidgetBottomHorziontalSubLayout2.addWidget(self.vaultLocationLine)
        self.treeWidgetBottomHorziontalSubLayout2.addWidget(self.importVaultButton)

        def treeWidgetModifyLocationAndExtension(file_path : str) -> None:
            self.vaultLocationLine.setText(file_path)
            self.vaultExtensionLine.setText(file_path[file_path.rfind('.'):])
        self.treeWidget.clicked_file_signal.connect(treeWidgetModifyLocationAndExtension)

        # Merge Bottom into main
        self.treeWidgetBottomVerticalLayout1.addLayout(self.treeWidgetBottomHorziontalSubLayout1)
        self.treeWidgetBottomVerticalLayout1.addLayout(self.treeWidgetBottomHorziontalSubLayout2)
        self.vertical_div.addLayout(self.treeWidgetBottomVerticalLayout1)

        # Unknown
        self.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)


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
        if(not cwd):
            current_directory = os.getcwd()
        else:
            current_directory = cwd
        for root, dirs, files in os.walk(current_directory):
            for file in files:
                if file.endswith(vault_extension):
                    return (os.path.join(root, file))
        return None

    # Button detect handle results
    def on_detect_button_clicked(self, vault_extension: str) -> None:
        """Attempts to find the given vault_extension in the displayed working dir with a seperate thread.
        Updates vaultLocationLine with `Not Found` or the vault location

        Args:
            vault_extension (str): vault_extension aka .vault
        """
        extension = vault_extension.replace(" ", "")
        if not is_proper_extension(extension):
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Vault extension")
            message_box.showMessage(f"The extension: '{extension}' of the vault is invalid!")
            return
        for t in self.threads:
            if(t.handled_function == "detect_vault" and not t.timer_finished):
                self.logger.info(f"{t} is Already running with {t.handled_function}")
                return

        self.mythread = CustomThread(10 , self.detect_vault.__name__)
        self.threads.append(self.mythread)
        self.worker = Worker(self.detect_vault, vault_extension, self.treeWidget.current_path)

        self.worker.moveToThread(self.mythread)
        self.mythread.started.connect(self.worker.run)

        self.worker.finished.connect(self.mythread.stop_timer)
        self.worker.finished.connect(self.mythread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        #self.worker.finished.connect(self.mythread.deleteLater) _ PLACEHOLDER TODO

        # Progress functions
        def update_detected_file(emitted_obj : object) -> None:
            self.vaultLocationLine.setText(str(emitted_obj))

        def update_detected_button_progress(emitted_num : int) -> None:
            if emitted_num == 100 or self.detectVaultButtonProgressBar.value() == 100:
                self.detectVaultButtonProgressBar.stop_progress()
                return
            if self.detectVaultButtonProgressBar.value() == 0:
                self.detectVaultButtonProgressBar.setVisible(True)
            current_value = self.detectVaultButtonProgressBar.value()
            self.detectVaultButtonProgressBar.setValue(emitted_num + current_value)

        self.mythread.progress.connect(update_detected_button_progress)
        self.mythread.timeout_signal.connect(update_detected_file)
        self.mythread.finished.connect(self.mythread.quit)
        #self.mythread.finished.connect(self.mythread.deleteLater) _ PLACEHOLDER TODO

        self.mythread.start()

    # Button reset handle results
    def on_reset_button_clicked(self) -> None:
        """Reset all fields visible on the Window to empty strings. Also resets the TreeView
        """
        current_drive = self.driveDropdown.currentText()
        self.treeWidgetAddressBar.setText(current_drive)
        self.vaultExtensionLine.setText("")
        self.treeWidget.populate(current_drive)
        self.passwordLineEdit.get_passwordLine().setText("")
        self.vaultLocationLine.setText("")

    # Button import handle results
    def on_import_button_clicked(self) -> None:
        """Logic to import vault
        """
        password = self.passwordLineEdit.get_passwordLine().text()
        vault_loc = self.vaultLocationLine.text()
        vault_extension = self.vaultExtensionLine.text().replace(" ", "")

        message_box = CustomMessageBox(parent=self)
        if not password:
            message_box.setIcon(QMessageBox.Icon.Critical)
            message_box.setWindowTitle("No Password")
            message_box.showMessage("Password field is empty!")
        elif not vault_loc:
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Unknown vault location")
            message_box.showMessage("No vault location has been chosen!")
        elif not is_proper_extension(vault_extension):
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Vault Extension")
            message_box.showMessage("The extension of the vault is not correct!")
        elif not vault_extension == vault_loc[vault_loc.rfind('.'):]:
            message_box.setIcon(QMessageBox.Icon.Critical)
            message_box.setWindowTitle("Vault Extension")
            message_box.showMessage(f"The extension of the vault: '{vault_extension}' does not correspond to the extension of '{vault_loc}'!")
        else:
            # Do import logic here _ PLACEHOLDER TODO
            print(f"Password: {password} - Vault location: {vault_loc} - Extension: {vault_extension}. NOW FIX IT")
            #self.exit()

    # Button insert handle results
    def on_insert_button_clicked(self, path : str) -> None:
        """If there is path added by the user, then update the tree view with it

        Args:
            path (str): Path given by the user
        """
        if not path:
            return
        self.treeWidgetAddressBar.setText(path)
        drive = path[0] + ":\\" # Edge case when drive is only selected, first letter is taken
        for i in range(self.driveDropdown.count()):
            if drive == self.driveDropdown.itemText(i):
                self.driveDropdown.setCurrentIndex(i)
                break
        self.treeWidget.populate(path)

    # Button detect handle results
    def handle_detect_vault_result(self, result : str) -> None:
        """Update the vault location line with the emitted value from the sub thread

        Args:
            result (str): Result is the emitted value from the sub thread searching for the vault in the current directory
        """
        self.vaultLocationLine.setText(result)

    # Cleanup
    def exit(self) -> None:
        """Cleans up any available threads and tries to close them along with the window.
        """
        for t in self.threads:
            t.exit()
        self.threads.clear()
        print(self.hide())
        print(self.close())
        print(self.destroy())
        print("Exit the window  _ PLACEHOLDER TODO")

