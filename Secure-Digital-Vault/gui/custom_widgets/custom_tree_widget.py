from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, QFileIconProvider, QStyle
from PyQt6.QtCore import QDir, QFileInfo, Qt , pyqtSignal
from PyQt6.QtGui import QMouseEvent , QKeyEvent, QIcon
from utils.parsers import parse_size_to_string, get_available_drives, parse_timestamp_to_string
from utils.extractors import get_file_from_vault, extract_icon_from_bytes
from classes.file import File
from classes.directory import Directory
from logger.logging import Logger

class CustomTreeWidget(QTreeWidget):
    """
    Customized QTreeWidget for displaying file system information.

    Parameters:
        columns (int): The number of columns for the tree widget. Default is 4.
        parent (QWidget): The parent widget. Default is None.
    """
    updated_signal = pyqtSignal(object)
    clicked_file_signal = pyqtSignal(object)

    def __init__(self, columns: int = 4, vaultview : bool = False , vaultpath : str = None, header_map : dict = None, parent: QWidget = None):
        """
        Initialize the custom tree widget.

        Args:
            columns (int): The number of columns for the tree widget. Default is 4.
            vaultview (bool): boolean indicating that the tree widget is meant for VaultView
            vaultpath (str): location of the vault on the disk
            header_map(dict): the header_map dictionary
            parent (QWidget): The parent widget. Default is None.
        """
        super().__init__(parent)
        self.vaultview = vaultview
        self.__vaultpath = vaultpath
        self.__header_map = header_map

        self.setColumnCount(columns)
        self.headers=["Name", "Type", "Size", "Data Modified"]
        self.setHeaderLabels(self.headers)
        self.resize_columns(50)
        self.itemDoubleClicked.connect(self.handle_double_clicked)

        self.current_held_item = self.currentItem()
        self.current_path = None

    def update_vaultpath(self, vaultpath : str) -> None:
        """Updates the vault path field

        Args:
            vaultpath (str): Value to update vaultpath with
        """
        self.__vaultpath = vaultpath

    def update_header_map(self, header_map : dict) -> None:
        """Updates the vault path field

        Args:
            header_map (dict): Value to update header_map with
        """
        self.header_map = header_map


    def update_columns_with(self, lst : list[str]) -> None:
        """Updates the tree's columns and column count

        Args:
            lst (list[str]): List of column headers
        """
        for header in lst:
            self.headers.append(header)
        self.setColumnCount(len(self.headers))
        self.setHeaderLabels(self.headers)
        self.resize_columns(50)

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

    def populate_from_header(self, header_map : dict, current_path : str, vault_path : str) -> None:
        """Populates the tree widget from the map data

        Args:
            header_map (dict): map dict from the header
            vault_path (str): location of the vault in order to extract icons
        """
        self.clear()
        files = set()
        if current_path != "/":
            item = QTreeWidgetItem([".."])
            item.file_path = Directory.determine_parent(None,current_path)
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent)
            item.setText(1, "UpOneLevel")
            item.setIcon(0, icon)
            self.addTopLevelItem(item)

        # Directories first
        for dir in header_map["directories"]:
            if dir["directory"]["path"] == current_path:
                directory = Directory(dir["directory"])
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
                item = QTreeWidgetItem([directory.get_name()])
                item.file_path = f"{directory.get_path()}{directory.get_name()}/"  # file_path indicates where it goes, path itself is where it exists
                item.setIcon(0, icon)                                              # e.g, get_path() = '/path/' , get_name() = 'name' -> /path/name
                self.set_item_text(item, directory)
                self.addTopLevelItem(item)
                for file_id in directory.get_files():
                    files.add(file_id)

        # Files second
        for entry in header_map["files"]:
            if entry["file"]["id"] in files:
                file = File(entry["file"])
                item = QTreeWidgetItem([file.get_metadata()["name"]])
                icon_bytes = get_file_from_vault(vault_path,file.get_metadata()["icon_data_start"],file.get_metadata()["icon_data_end"])
                icon = extract_icon_from_bytes(icon_bytes)
                item.file_path = file.get_path()
                item.setIcon(0, icon)
                self.set_item_text(item, file)
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

    def set_item_text(self, item: QTreeWidgetItem, entry) -> None:
        """
        Set text and icons for each item in the tree widget based on file information.

        Args:
            item (QTreeWidgetItem): The item to set text and icons for.
            entry (QFileInfo or File or Directory): The class which holds the information used to set the text and icons.
        """
        text_mappings = {}
        if isinstance(entry, QFileInfo):
            text_mappings = {
                1: "Folder" if entry.isDir() else entry.completeSuffix(),
                2: parse_size_to_string(entry.size()),
                3: entry.lastModified().toString("dd-MMM-yy HH:mm"),
                4: "PLACEHOLDER"
            }
        elif isinstance(entry, File):
            text_mappings = {
                1: entry.get_metadata()["type"],
                2: parse_size_to_string(entry.get_size()),
                3: parse_timestamp_to_string(entry.get_metadata()["last_modified"]),
                4: parse_timestamp_to_string(entry.get_metadata()["data_created"]),
            }
        elif isinstance(entry, Directory):
            text_mappings = {
                1: "Folder",
                2: str(0),
                3: "",
                4: parse_timestamp_to_string(entry.get_data_created())
            }
        if item.text(0) == "..":
            item.setText(1, "UpOneLevel")
            item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent))
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
            print("Double clicked a folder.",item.text(0),item.text(1),item.file_path)
            child_path = item.file_path
            if child_path:
                self.updated_signal.emit(child_path)
                if self.vaultview:
                    self.populate_from_header(header_map=self.__header_map, current_path=child_path,vault_path=self.__vaultpath)
                else:
                    self.populate(child_path)
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
                if self.vaultview:
                    self.populate_from_header(header_map=self.__header_map, current_path=parent_path,vault_path=self.__vaultpath)
                else:
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
                    if self.vaultview:
                        self.populate_from_header(header_map=self.__header_map, current_path=parent_path,vault_path=self.__vaultpath)
                    else:
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
