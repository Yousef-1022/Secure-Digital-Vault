from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QHBoxLayout, QMessageBox
from PyQt6.QtGui import QIcon

from gui.custom_widgets.custom_messagebox import CustomMessageBox
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line_password import CustomPasswordLineEdit

from utils.constants import ICON_14, ICON_1

class InteractDialog(QDialog):

    def __init__(self, parent : QWidget):
        super().__init__(parent)
        self.setWindowTitle("User Input")

        self.__command = "Skip"
        self.__data = ""

        self.vertical_layout = QVBoxLayout(self)
        self.horizontal_layout = QHBoxLayout()

        # Password
        self.password_string_label = QLabel("File encrypted! Password:", self)
        self.password_line_edit = CustomPasswordLineEdit(placeholder_text="File password", parent=self)

        # Proceed button
        self.proceed_button = CustomButton("Proceed", QIcon(ICON_1), "Continue with the extraction by giving the password" ,self)
        self.proceed_button.clicked.connect(self.__proceed_with_extraction)

        # Skip button
        self.skip_button = CustomButton("Skip", QIcon(ICON_14), "Skip the given file from extraction" ,self)
        self.skip_button.clicked.connect(self.__skip_with_extraction)

        # Merge divs
        self.vertical_layout.addWidget(self.password_string_label)
        self.vertical_layout.addWidget(self.password_line_edit)

        self.horizontal_layout.addWidget(self.proceed_button)
        self.horizontal_layout.addWidget(self.skip_button)

        self.vertical_layout.addLayout(self.horizontal_layout)

    def get_data(self) -> object:
        """Gets the data used for interaction

        Returns:
            Object: The data used to interact
        """
        return self.__data

    def set_data(self , data : object) -> None:
        """Sets the data used for interaction

        Args:
            data (object): The data used to interact
        """
        self.__data = data

    def get_command(self) -> object:
        """Gets the command used for interaction

        Returns:
            object: The command used for interaction
        """
        return self.__command

    def set_command(self, command : object) -> None:
        """Sets the command used for interaction

        Args:
            command (object): The command used for interaction
        """
        self.__command = command

    def __proceed_with_extraction(self) -> None:
        """Lets the parent widget proceed with the interaction by giving it the required parameters
        """
        if not self.password_line_edit.get_passwordLine().text():
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Critical)
            message_box.setWindowTitle("Empty password")
            message_box.showMessage("The password cannot be empty!")
            self.reset_inner_items()
            return

        self.__command = "Proceed"
        self.__data = self.password_line_edit.get_passwordLine().text()
        self.close()

    def __skip_with_extraction(self) -> None:
        """Lets the parent widget skip with the extraction of the current item
        """
        self.__command = "Skip"
        self.__data = ""
        self.close()

    def reset_inner_items(self) -> None:
        """Sets the interaction items back to default
        """
        self.__command = "Skip"
        self.__data = ""
        self.password_string_label.setText("File encrypted! Password:")
        self.password_line_edit.get_passwordLine().setText("")
