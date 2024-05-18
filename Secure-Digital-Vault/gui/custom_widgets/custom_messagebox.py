from PyQt6.QtWidgets import QMessageBox, QPushButton, QWidget
from PyQt6.QtGui import QIcon
from utils.constants import ICON_1


class CustomMessageBox(QMessageBox):
    def __init__(self, title: str = None, message: str = None, icon_path: str = None, icon : QIcon = None , icon_box : QMessageBox.Icon = None, parent: QWidget = None):
        """
        Custom message box dialog.

        Parameters:
            title (str, optional): The title of the message box.
            message (str, optional): The main message text to display.
            icon_path (str, optional): Path to the icon to display in the message box title bar.
            icon (QIcon, optional): QIcon belonging to the widget requiring a messagebox
            icon_box (QMessageBox.Icon): The icon that shows inside the messagebox when release
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
        else:
            self.setWindowIcon(QIcon(ICON_1))

        if icon_box is not None:
            self.setIcon(icon_box)
        else:
            self.setIcon(QMessageBox.Icon.Information)
        self.setModal(False)
        self.addButton(QPushButton("OK"), QMessageBox.ButtonRole.AcceptRole)

    def showMessage(self, message : str, messages : list[str] = None) -> None:
        """
        Display a message in the message box and execute it.

        Args:
            message (str): The message to be displayed in the message box.
            messages(list[str]): The messages to be displayed in the message box.
        """
        if message and message != "":
            self.setText(message)
        else:
            self.setText("")
        if messages is not None:
            answer = self.text()
            for m in messages:
                answer += f"{m}\n"
            self.setText(answer)
        self.exec()

    def exit(self):
        """Close the message box."""
        self.close()
