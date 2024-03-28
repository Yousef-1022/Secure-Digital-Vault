from PyQt6.QtWidgets import QMessageBox, QPushButton, QWidget
from PyQt6.QtGui import QIcon

class CustomMessageBox(QMessageBox):
    def __init__(self, title: str = None, message: str = None, icon_path: str = None, icon : QIcon = None , parent: QWidget = None):
        """
        Custom message box dialog.

        Parameters:
            title (str, optional): The title of the message box.
            message (str, optional): The main message text to display.
            icon_path (str, optional): Path to the icon to display in the message box title bar.
            icon (QIcon, optional): QIcon belonging to the widget requiring a messagebox
            parent (QWidget, optional): The parent widget of the message box.
        """
        super().__init__(parent)
        if title is not None:
            self.setWindowTitle(title)
        if message is not None:
            self.setText(message)
        if icon is not None:
            self.setWindowIcon(icon)
        elif icon_path is not None:
            self.setWindowIcon(QIcon(icon_path))

        self.setIcon(QMessageBox.Icon.Information)
        self.setModal(False)
        self.addButton(QPushButton("OK"), QMessageBox.ButtonRole.AcceptRole)

    def showMessage(self, message : str) -> None:
        """
        Display a message in the message box and execute it.

        Args:
            message (str): The message to be displayed in the message box.
        """
        self.setText(message)
        self.exec()

    def exit(self):
        """Close the message box."""
        self.close()
