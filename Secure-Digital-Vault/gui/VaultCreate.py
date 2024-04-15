from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QStatusBar, QListWidget, QListWidgetItem, QLabel, QLineEdit, QProgressBar, QMessageBox
from PyQt6.QtGui import QIcon
from gui.custom_widgets.custom_line import CustomLine
from gui.custom_widgets.custom_button import CustomButton
from gui.custom_widgets.custom_line_password import CustomPasswordLineEdit
from gui.custom_widgets.custom_progressbar import CustomProgressBar
from logger.logging import Logger
from utils.constants import ICON_1

class VaultCreateWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window Data
        self.logger = Logger()
        self.threads = []

        # QtData
        self.setObjectName("Vault Creator")
        self.setWindowTitle("Vault Creator")
        self.setWindowIcon(QIcon(ICON_1))
        self.setMinimumWidth(640)
        self.setMinimumHeight(480)
        self.resize(640, 480)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralWidget")

        # Main Layout
        self.main_layout = QVBoxLayout(self.centralwidget)

        self.instruction_label = QLabel("Enter data and click 'Save' to save each item:", self)
        self.main_layout.addWidget(self.instruction_label)

        self.item_list_widget = QListWidget(self)
        self.main_layout.addWidget(self.item_list_widget)

        # Add items from the vault header to the list widget
        for i in range(3):
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)

            purpose_label = QLabel(f"Item {i + 1}:", self)
            item_layout.addWidget(purpose_label)

            input_field = CustomLine("", f"Enter data for Item {i + 1}", item_widget)
            item_layout.addWidget(input_field)

            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())  # Set the size of the item
            self.item_list_widget.addItem(list_item)
            self.item_list_widget.setItemWidget(list_item, item_widget)

        # Password requires recovery instructions
        password_widget = QWidget()
        password_layout = QHBoxLayout(password_widget)
        password_label = QLabel("Password:", self)
        password_layout.addWidget(password_label)
        password_field = CustomPasswordLineEdit("", parent=password_widget)
        password_layout.addWidget(password_field)
        password_item = QListWidgetItem()
        password_item.setSizeHint(password_widget.sizeHint())
        self.item_list_widget.addItem(password_item)
        self.item_list_widget.setItemWidget(password_item, password_widget)

        # Save or Edit button at the bottom
        self.save_edit_button = CustomButton("Save", QIcon(ICON_1), "Save items", self)
        self.save_edit_button.set_action(self.save_or_edit)

        self.create_button = CustomButton("Create", QIcon(ICON_1), "Create something", self)
        self.create_button.set_action(self.create_something)

        # Horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_edit_button)
        button_layout.addWidget(self.create_button)

        self.main_layout.addLayout(button_layout)

        # Progress bar to indicate the creation of the vault.
        self.progress_bar = CustomProgressBar(is_visible_at_start=False)
        self.main_layout.addWidget(self.progress_bar)


        self.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

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
        for i in range(self.item_list_widget.count()):
            list_item = self.item_list_widget.item(i)
            item_widget = self.item_list_widget.itemWidget(list_item)
            if item_widget:
                input_field = item_widget.findChild(QLineEdit)
                if input_field:
                    input_field.setReadOnly(True)
        self.save_edit_button.setText("Edit")
        print("Works")
        #TODO

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
        #TODO

    def create_something(self):
        """Actual function to create the vault.
        """
        if self.save_edit_button.text() == "Save":
            QMessageBox.warning(self, "Unsaved Changes", "Please save your changes before creating the vault")
            return
        print("Hello, World!")
        self.progress_bar.setVisible(True)
        #TODO

