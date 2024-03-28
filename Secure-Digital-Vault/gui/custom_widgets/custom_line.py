from PyQt6.QtWidgets import QLineEdit, QWidget

class CustomLine(QLineEdit):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
