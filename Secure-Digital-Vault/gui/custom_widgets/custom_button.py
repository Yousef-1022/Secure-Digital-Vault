from PyQt6.QtWidgets import QPushButton, QSizePolicy, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from gui.custom_widgets.custom_messagebox import CustomMessageBox

class CustomButton(QPushButton):
    def __init__(self, label: str, icon: QIcon, info_text: str, parent: QWidget = None):
        """
        CustomButton constructor.

        Parameters:
            label (str): The label text for the button.
            icon_path (str): The file path to the button icon.
            info_text (str): The text to display in the information box.
            parent (QWidget): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setIcon(icon)
        self.setText(label)
        self.button_label = label
        self.info_text = info_text
        self.actual_parent = parent
        self.custom_message_box = None
        self.action_function = None

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.clicked.connect(self.default_action)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.set_show_details)

    def set_action(self, action_function, *args, **kwargs) -> None:
        """
        Set a custom action for the button.

        Parameters:
            action_function (callable): The function to be executed when the button is clicked.
            *args: Positional arguments to pass to the action function.
            **kwargs: Keyword arguments to pass to the action function.
        """
        #self.clicked.connect(lambda: action_function(*args, **kwargs)) PLACEHOLDER
        def action_func_then_exit():
            action_function(*args, **kwargs)
            self.exit()
        self.clicked.disconnect(self.default_action)  # Disconnect default action
        self.clicked.connect(action_func_then_exit)

    def set_custom_css(self, css: str) -> None:
        """
        Set custom CSS for styling the button.

        Parameters:
            css (str): The CSS stylesheet to apply to the button.
        """
        self.setStyleSheet(css)

    def default_action(self) -> None:
        """
        Default action triggered when the button is clicked.
        """
        self.exit()

    def set_show_details(self) -> None:
        """
        Show details in a custom message box when the button is right-clicked.
        """
        if (not self.custom_message_box):
            self.custom_message_box = CustomMessageBox(title=f"{self.button_label} Button Details", message=self.info_text, icon=self.icon(), parent=self.actual_parent)
        if(not self.custom_message_box.isVisible()):
            self.custom_message_box.show()

    def exit(self) -> None:
        """
        Exit function to close the custom message box if open.
        """
        for obj in self.actual_parent.children():
            if(self.custom_message_box and obj==self.custom_message_box):
                self.custom_message_box.exit()
