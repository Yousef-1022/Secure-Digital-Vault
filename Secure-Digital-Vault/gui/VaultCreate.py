from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QListWidget, QListWidgetItem, QLabel, QLineEdit, QMessageBox
from PyQt6.QtGui import QIcon

from gui import ViewManager
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line_password import CustomPasswordLineEdit
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from gui.custom_widgets.custom_messagebox import CustomMessageBox

from logger.logging import Logger
from file_handle.file_io import append_bytes_into_file, add_magic_into_header, header_padder, add_magic_into_footer

from utils.constants import VAULT_CREATION_KEYS , ICON_8, ICON_3, ICON_5, MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT, VAULT_BUFFER_LIMIT
from utils.serialization import serialize_dict, formulate_header, formulate_footer
from utils.helpers import is_proper_extension, is_location_ok
from utils.parsers import parse_file_name

from crypto.utils import is_password_strong, xor_magic, to_base64
from crypto.encryptors import encrypt_header, encrypt_footer, generate_password_token


class VaultCreateWindow(QMainWindow):
    def __init__(self , VaultViewManager : ViewManager):
        super().__init__()

        # Pointer to ViewManager
        self.__view_manager = VaultViewManager
        # Window Data
        self.threads = []

        # QtData
        self.setObjectName("Vault Creator")
        self.setWindowTitle("Vault Creator")
        self.setWindowIcon(QIcon(ICON_3))
        self.setMinimumWidth(MINIMUM_WINDOW_WIDTH)
        self.setMinimumHeight(MINIMUM_WINDOW_HEIGHT)
        self.resize(800, 600)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Main Layout
        self.main_layout = QVBoxLayout(self.centralwidget)

        self.instruction_label = QLabel("Enter data and click 'Save' to save each item:", self)
        self.main_layout.addWidget(self.instruction_label)

        self.item_list_widget = QListWidget(self)
        self.main_layout.addWidget(self.item_list_widget)

        # Add items from the vault header to the list widget
        self.max_label_width = 0
        for i in VAULT_CREATION_KEYS:

            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)

            purpose_label = QLabel(f"{i}:", self)
            label_width = purpose_label.fontMetrics().boundingRect(purpose_label.text()).width()
            self.max_label_width = max(self.max_label_width, label_width)
            item_layout.addWidget(purpose_label)

            input_field = CustomLine("", f"Enter data for the {i}", item_widget)
            input_field.set_representing(i)
            item_layout.addWidget(input_field)

            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())  # Set the size of the item
            self.item_list_widget.addItem(list_item)
            self.item_list_widget.setItemWidget(list_item, item_widget)

        # Label size management
        for i in range(self.item_list_widget.count()):
            list_item = self.item_list_widget.item(i)
            item_widget = self.item_list_widget.itemWidget(list_item)
            purpose_label = item_widget.findChild(QLabel)
            purpose_label.setMinimumWidth(self.max_label_width)

        # Password requires recovery instructions
        self.password_widget = QWidget()
        self.password_layout = QHBoxLayout(self.password_widget)
        self.password_label = QLabel("Password:", self)
        self.password_layout.addWidget(self.password_label)
        self.password_field = CustomPasswordLineEdit("", parent=self.password_widget)
        self.password_layout.addWidget(self.password_field)
        self.password_item = QListWidgetItem()
        self.password_item.setSizeHint(self.password_widget.sizeHint())
        self.item_list_widget.addItem(self.password_item)
        self.item_list_widget.setItemWidget(self.password_item, self.password_widget)

        # Buttons
        self.return_button = CustomButton("Return", QIcon(ICON_3), "Return to MainMenu", self)
        self.return_button.set_action(self.__open_view_manager)

        # Save or Edit button at the bottom
        self.save_edit_button = CustomButton("Save", QIcon(ICON_5), "Save items", self)
        self.save_edit_button.set_action(self.save_or_edit)

        self.create_button = CustomButton("Create", QIcon(ICON_8), "Create something", self)
        self.create_button.set_action(self.create_vault)

        # Horizontal layout for buttons
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.return_button)
        self.button_layout.addWidget(self.save_edit_button)
        self.button_layout.addWidget(self.create_button)

        self.main_layout.addLayout(self.button_layout)

        # Progress bar to indicate the creation of the vault.
        self.progress_bar = CustomProgressBar(is_visible_at_start=False)
        self.main_layout.addWidget(self.progress_bar)


        # Additional information labels can be added here
        self.setCentralWidget(self.centralwidget)

    def save_or_edit(self):
        """Function used to save the data available in the list in order not allow modification.
        """
        button_text = self.save_edit_button.text()
        if button_text == "Save":
            self.save_items()
        else:
            self.edit_items()

    def save_items(self):
        """Helper function to keep the items uneditable after saving
        """
        valid_fields = self.check_items()
        if valid_fields:
            valid_password = self.check_password(self.password_field.get_passwordLine().text())
            if valid_password:
                for i in range(self.item_list_widget.count()):
                    list_item = self.item_list_widget.item(i)
                    item_widget = self.item_list_widget.itemWidget(list_item)
                    if item_widget:
                        input_field = item_widget.findChild(QLineEdit)
                        if input_field:
                            input_field.setReadOnly(True)
                self.save_edit_button.setText("Edit")

    def edit_items(self):
        """Helper function to allow the items to be edtiable after saving
        """
        for i in range(self.item_list_widget.count()):
            list_item = self.item_list_widget.item(i)
            item_widget = self.item_list_widget.itemWidget(list_item)
            if item_widget:
                input_field = item_widget.findChild(QLineEdit)
                if input_field:
                    input_field.setReadOnly(False)
        self.save_edit_button.setText("Save")

    def check_items(self) -> bool:
        """Investigates whether the items given for the vault creation are valid without the password.

        Returns:
            bool: True if no items contain invalid data, False otherwise.
        """
        errors = ""
        for i in range(self.item_list_widget.count()):
            list_item = self.item_list_widget.item(i)
            item_widget = self.item_list_widget.itemWidget(list_item)
            line = item_widget.findChild(CustomLine)
            if line:
                item_text = line.get_representing()
                # Vault Name
                if item_text == VAULT_CREATION_KEYS[0]:
                    if line.text() == "":
                        errors += f"- {item_text} must not be empty!\n"
                    elif not (res := parse_file_name(line.text()))[0]:
                        errors += f"- {res[1]}\n"
                # Extension
                elif item_text == VAULT_CREATION_KEYS[1] and not is_proper_extension(line.text()):
                    errors += f"- {item_text} '{line.text()}' is invalid! Valid example: '.vault'.\n"
                # Save Location
                elif item_text == VAULT_CREATION_KEYS[2]:
                    v = is_location_ok(line.text(), for_file_save=True, for_file_update=False)
                    if not v[0]:
                        errors+=f"- {v[1]}\n"
                # Password Hint
                elif item_text == VAULT_CREATION_KEYS[3]:
                    if line.text() == "":
                        errors+=f"- {item_text} must not be empty!"
                    elif len(line.text()) > 32:
                        errors+=f"- {item_text} must be less than 32 characters!"

        if len(errors) != 0:
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Vault Creation Data")
            message_box.showMessage(errors)
            return False
        return True

    def check_password(self, password : str) -> bool:
        """Checks whether the password is valid or not

        Args:
            password (str): Given Password

        Returns:
            bool: True if password is good, False if password is invalid.
        """
        result = is_password_strong(password)
        if result[0]:
            return True
        message_box = CustomMessageBox(parent=self)
        message_box.setIcon(QMessageBox.Icon.Critical)
        message_box.setWindowTitle("Vault Creation Data")
        message_box.showMessage("",result[1])
        return False

    def create_vault(self):
        """Actual function to create the vault.
        """
        if self.save_edit_button.text() == "Save":
            QMessageBox.warning(self, "Unsaved Changes", "Please save your changes before creating the vault")
            return
        self.progress_bar.setVisible(True)

        # Header
        data = self.__collect_header_data()
        vault = f"{data['Vault Name']}{data['Vault Extension']}"
        header = serialize_dict(formulate_header(data["Vault Name"] , data["Vault Extension"]))
        header = encrypt_header(data["Password"], header)
        header = add_magic_into_header(header)
        self.progress_bar.setValue(30)
        result = append_bytes_into_file(file_path=data['Vault Location'], the_bytes=header,create_file=True, file_name=vault)
        if not result[0]:
            QMessageBox.warning(self, "Couldn't create vault", f"Reason: {result[1]}")
            self.progress_bar.setVisible(False)
            self.progress_bar.setValue(0)
            return
        self.progress_bar.setValue(60)

        # Footer + Hint
        footer = formulate_footer()
        first_log = Logger.form_log_message(f'Vault {vault} created!\n')
        footer["session_log"] += first_log
        footer = serialize_dict(footer)
        footer = encrypt_footer(data["Password"], footer)
        footer = add_magic_into_footer(footer) + xor_magic(data['Password Hint'])
        result = append_bytes_into_file(file_path=f"{data['Vault Location']}/{vault}", the_bytes=footer, create_file=False)
        if not result[0]:
            QMessageBox.warning(self, "Couldn't finish creating the vault", f"Reason: {result[1]}")
            self.progress_bar.setVisible(False)
            self.progress_bar.setValue(0)
            return
        self.progress_bar.setValue(90)

        # Padding
        header_padder(file_path=f"{data['Vault Location']}/{vault}", amount_to_pad=VAULT_BUFFER_LIMIT) # buffer size

        # Tokens
        location_for_tokens = data["Vault Location"]

        self.__generate_tokens(data["Password"], location_for_tokens)

        message_box = CustomMessageBox(parent=self)
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setWindowTitle("Vault Special Tokens")
        message_box.showMessage(f"Please find the special Vault tokens which can be used as recovery in {location_for_tokens}/tokens.txt")
        message_box.deleteLater()
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

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

    def __collect_header_data(self) -> dict:
        """Gets the necessary information for the header, and attaches the hint to the end of this dict

        Returns:
            dict: Returns the required data to make a header
        """
        result_dict = {}
        result_dict["Password"] = self.password_field.get_passwordLine().text()
        for i in range(self.item_list_widget.count()):
            list_item = self.item_list_widget.item(i)
            item_widget = self.item_list_widget.itemWidget(list_item)
            line = item_widget.findChild(CustomLine)
            if line:
                result_dict[line.get_representing()] = line.text()
        return result_dict

    def __open_view_manager(self):
        self.__view_manager.signal_to_open_window.emit("")

    def closeEvent(self, event):
        """Override for close window incase import is running.
        """
        if self.__view_manager:
            self.__view_manager.signal_to_open_window.emit("")
            self.__view_manager = None
        self.exit()
        super().closeEvent(event)

    def exit(self) -> None:
        """Cleans up any available threads and tries to close them along with the window.
        """
        self.__view_manager = None
        for t in self.threads:
            t.exit()
        self.threads.clear()
        self.hide()
        self.close()
