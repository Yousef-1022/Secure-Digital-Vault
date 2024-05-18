from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import pyqtSignal

class PopupWindow(QWidget):

    signal_for_destruction = pyqtSignal(object)

    """PopupWindow to view Logs

    Args:
        QWidget (Parent): Optional Parent Widget
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()
        self.__message = QLabel("Check Logs", self)
        self.__message.setStyleSheet("background-color: rgba(0, 0, 0, 200); color: white; padding: 10px; border-radius: 10px;")

        layout.addWidget(self.__message)
        self.setLayout(layout)

        self.__timer = QTimer(self)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.exit)

    def set_message(self, message : str):
        """Sets the message of the the window

        Args:
            message (str): Message to view in popup. Defaults to "Check Logs".
        """
        if message:
            self.__message.setText(message)
        else:
            self.__message.setText("Check Logs")

    def stop_and_reset_timer(self):
        """Stops the running timer and resets it
        """
        if self.__timer:
            self.__timer.stop()

    def show_with_timeout(self, timeout : int = 3000):
        """Shows the log message with a timeout of 3 seconds

        Args:
            timeout (int, optional): Amount of miliseconds before time out to closure. Defaults to 3000.
        """
        self.show()
        self.__timer.start(timeout)

    def exit(self):
        """Cleans up any data in the window
        """
        if self.__timer:
            try:
                self.__timer.stop()
                self.__timer.deleteLater()
            except RuntimeError:
                pass
        self.__timer = None
        self.hide()
        self.close()
        self.signal_for_destruction.emit("Destroy")
