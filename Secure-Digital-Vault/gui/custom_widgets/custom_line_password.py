from PyQt6.QtWidgets import QLineEdit, QWidget, QHBoxLayout
from PyQt6.QtGui import QIcon
from gui.custom_widgets.custom_button import CustomButton
from utils.constants import ICON_7

class CustomPasswordLineEdit(QWidget):
    def __init__(self, placeholder_text: str = None, icon_path: str = None, icon: QIcon = None, parent: QWidget = None):
        """
        Custom widget to represent (QLineEdit) for a password line edit with an eye icon button to toggle visibility.

        Args:
            placeholder_text (str, optional): Placeholder text for the password line edit.
            icon_path (str, optional): Path to the eye icon image file.
            icon (QIcon, optional): QIcon for the eye icon button.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)

        self.__passwordLine = QLineEdit(self)
        if placeholder_text is None:
            self.__passwordLine.setPlaceholderText("Vault password")
        else:
            self.__passwordLine.setPlaceholderText(placeholder_text)
        self.__passwordLine.setEchoMode(QLineEdit.EchoMode.Password)

        # Eye icon button to toggle password visibility
        self.eyeButton = CustomButton("", QIcon(ICON_7), "Show password", self)
        if icon_path is not None:
            self.eyeButton.setIcon(QIcon(icon_path))
        elif icon is not None:
            self.eyeButton.setIcon(icon)
        self.eyeButton.setCheckable(True)
        self.eyeButton.setChecked(False)  # Initially not checked

        # Set up layout
        layout = QHBoxLayout(self)
        layout.addWidget(self.__passwordLine)
        layout.addWidget(self.eyeButton)

        # Connect the eye button's toggled signal to toggle password visibility
        self.eyeButton.toggled.connect(self.toggle_password_visibility)

    def toggle_password_visibility(self, checked):
        """Toggles the visibility of the password text based on the state of the eye button."""
        if checked:
            self.__passwordLine.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.__passwordLine.setEchoMode(QLineEdit.EchoMode.Password)

    def get_passwordLine(self) -> QLineEdit:
        """Returns the QLineEdit object for the password line edit."""
        return self.__passwordLine
