from PyQt6.QtWidgets import QLineEdit, QWidget

class CustomLine(QLineEdit):
    def __init__(self, text : str, place_holder_text : str , parent: QWidget = None):
        """QLineEdit extension

        Args:
            text (str): current text to display on the line
            place_holder_text (str): place holder text to display on the line
            parent (QWidget, optional): parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setText(text)
        self.setPlaceholderText(place_holder_text)
