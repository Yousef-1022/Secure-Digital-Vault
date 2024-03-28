from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, QFileIconProvider, QStyle
from PyQt6.QtCore import QDir, QFileInfo, Qt , pyqtSignal
from PyQt6.QtGui import QMouseEvent , QKeyEvent
from utils.locators_and_parsers import parse_size_to_string, get_available_drives

class CustomTreeWidget(QTreeWidget):
    """
    Customized QTreeWidget for displaying file system information.

    Parameters:
        columns (int): The number of columns for the tree widget. Default is 4.
        parent (QWidget): The parent widget. Default is None.
    """
    updated_signal = pyqtSignal(object)
    clicked_file_signal = pyqtSignal(object) 

    def __init__(self, columns: int = 4, parent: QWidget = None):
        """
        Initialize the custom tree widget.

        Args:
            columns (int): The number of columns for the tree widget. Default is 4.
            parent (QWidget): The parent widget. Default is None.
        """
        super().__init__(parent)
        self.setColumnCount(columns)
        self.headers=["Name", "Type", "Size", "Data Modified"]
        self.setHeaderLabels(self.headers)
        self.itemDoubleClicked.connect(self.handle_double_clicked)

        self.current_held_item = self.currentItem()
        self.current_path = None

    def populate(self, path: str) -> None:
        """
        Populate the tree widget with file system information from the given path.

        Args:
            path (str): The path of the directory to populate.
        """
        if not path:
            return
        directory = QDir(path)
        drive = path[0] + ":\\" # Edge case when drive is only selected, first letter is taken
        if not directory.exists() or (drive not in get_available_drives()) or (len(path) < 3):
            return
        self.current_path = path
        self.clear()
        directory.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDot)
        file_icon_provider = QFileIconProvider()

        for entry in directory.entryInfoList():
            item = QTreeWidgetItem([entry.fileName()])
            item.setIcon(0, file_icon_provider.icon(entry))
            item.file_path = entry.absoluteFilePath()  # Store file path as an attribute

            # Populate additional columns and add the item directly to the tree widget
            self.set_item_text(item, entry)
            self.addTopLevelItem(item)
        self.resize_columns(50)

    def resize_columns(self, extra_pixels : int = 0) -> None:
        """Resizes the columns to fit the data nicely with a little extra space
        """
        for i in range(self.columnCount()):
            width = self.columnWidth(i)
            content_width = self.sizeHintForColumn(i)
            if content_width > width:
                self.setColumnWidth(i, content_width + extra_pixels)


    def set_item_text(self, item: QTreeWidgetItem, entry: QFileInfo) -> None:
        """
        Set text and icons for each item in the tree widget based on file information.

        Args:
            item (QTreeWidgetItem): The item to set text and icons for.
            entry (QFileInfo): The file information used to set the text and icons.
        """
        text_mappings = {
            1: "Folder" if entry.isDir() else entry.completeSuffix(),
            2: parse_size_to_string(entry.size()),
            3: entry.lastModified().toString("dd-MMM-yy HH:mm"),
            4: "PLACEHOLDER"
        }
        if item.text(0) == "..":
            item.setText(1, "UpOneLevel")
            item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
            self.current_held_item = item
        else:
            for i in range(1, self.columnCount()):
                if i == 2 and item.text(1) == "Folder":
                    continue
                else:
                    item.setText(i, text_mappings.get(i, ""))

    def handle_double_clicked(self, item: QTreeWidgetItem) -> None:
        """
        Handle double-click events on tree widget items.

        Args:
            item (QTreeWidgetItem): The item that was double-clicked.
        """
        if item.text(1) == "Folder" or item.text(1) == "UpOneLevel":
            print("Double clicked a folder.",item.text(0),item.text(1))
            parent_path = item.file_path
            if parent_path:
                self.updated_signal.emit(parent_path)
                self.populate(parent_path)
        else:
            print("Double clicked something else.",item.text(0),item.text(1))

    def mousePressEvent(self, event : QMouseEvent) -> None:
        """
        Handle mouse press events, and send a signal to update vault location widget if a file is clicked

        Args:
            event (QMouseEvent): The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
            self.current_held_item = self.itemAt(event.pos())
        super().mousePressEvent(event)
        if self.currentItem() and self.currentItem().text(1) not in ["Folder", "UpOneLevel"]:
            self.clicked_file_signal.emit(self.currentItem().file_path)

    def keyPressEvent(self, event : QKeyEvent):
        """Handle Enter Key and Backspace Key press

        Args:
            event (QKeyEvent): Enter Key clicked
        """
        if event.key() == Qt.Key.Key_Return and self.currentItem():
            parent_path = self.currentItem().file_path
            if self.currentItem().text(1) in ("Folder", "UpOneLevel"):
                self.updated_signal.emit(parent_path)
                self.populate(parent_path)
            else:
                self.clicked_file_signal.emit(parent_path)
        elif event.key() == Qt.Key.Key_Backspace:
            first_item = self.topLevelItem(0)
            if first_item and first_item.text(0) == "..":
                self.setCurrentItem(first_item)
                parent_path = first_item.file_path
                if parent_path:
                    self.updated_signal.emit(parent_path)
                    self.populate(parent_path)
        else:
            super().keyPressEvent(event)


    def get_current_held_item(self) -> QTreeWidgetItem:
        """
        Get the currently held item.

        Returns:
            QTreeWidgetItem: The currently held item.
        """
        return self.current_held_item
