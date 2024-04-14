from PyQt6.QtWidgets import QTreeWidget, QWidget, QFileIconProvider, QStyle
from PyQt6.QtCore import QDir, QFileInfo, Qt , pyqtSignal
from PyQt6.QtGui import QMouseEvent , QKeyEvent, QIcon

from utils.parsers import parse_size_to_string, get_available_drives, parse_timestamp_to_string
from utils.extractors import get_file_from_vault, extract_icon_from_bytes

from classes.file import File
from classes.directory import Directory
from logger.logging import Logger

from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem


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

    def get_vault_path(self):
        return self.__vaultpath

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
        print(f"Path: '{path}'")
        if not path:
            return
        directory = QDir(path)
        drive = path[0] + ":\\" # Edge case when drive is only selected, first letter is taken
        if not directory.exists() or (drive not in get_available_drives()) or (len(path) < 3):
            return
        self.clear()
        directory.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDot)
        file_icon_provider = QFileIconProvider()

        for entry in directory.entryInfoList():
            item = CustomQTreeWidgetItem([entry.fileName()])
            item.setIcon(0, file_icon_provider.icon(entry))
            item.set_path(entry.absoluteFilePath())   # Store file path as an attribute

            # Populate additional columns and add the item directly to the tree widget
            self.set_item_text(item, entry)
            self.addTopLevelItem(item)
        self.resize_columns(50)
        self.setCurrentItem(self.topLevelItem(0))

    def populate_from_header(self, header_map : dict, goto_dir : int, vault_path : str) -> bool:
        """Populates the tree widget from the map data

        Args:
            header_map (dict): map dict from the header
            goto_dir (int): go to path
            vault_path (str): location of the vault in order to extract icons

        Returns:
            bool: indicates whether the population with the goto_dir was valid
        """
        current_id = self.currentItem().get_path() if self.currentItem() is not None else 0
        if goto_dir > 0 and str(goto_dir) not in header_map["directories"].keys():
            return False

        cleard_once = False # Indicator to clear the tree once, this must be True if the directory is found
        skip_files = False  # Indicator incase the current directory does not have files

        cur_dir_name = Directory.determine_directory_path(path_id=goto_dir, data_dict=header_map["directories"])

        if cur_dir_name == "/":
            self.clear()
            cleard_once = True

        # Directories first which exist in goto_dir here
        for dir in header_map["directories"].values():
            if dir["path"] == goto_dir:

                # Add upto button first
                if not cleard_once:
                    self.clear()
                    cleard_once = True
                    upper_level = CustomQTreeWidgetItem([".."])
                    upper_level.set_path(Directory.determine_parent_by_id(current_id,header_map["directories"]))    # upper_level leads backwards
                    # TODO logger if file_path is invalid
                    icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent)
                    upper_level.setText(1, "UpOneLevel")
                    upper_level.setIcon(0, icon)
                    self.addTopLevelItem(upper_level)

                the_directory = Directory(dir)
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
                directory_item = CustomQTreeWidgetItem([the_directory.get_name()])
                directory_item.set_path(the_directory.get_id()) # the item must point to what's inside it.
                directory_item.setIcon(0, icon)
                directory_item.set_saved_obj(the_directory)
                self.set_item_text(directory_item, the_directory)
                self.addTopLevelItem(directory_item)

        # Case incase the directory does not have sub directories
        if not cleard_once:
            self.clear()
            cleard_once = True

            upper_level = CustomQTreeWidgetItem([".."])
            upper_level.set_path(Directory.determine_parent_by_id(current_id,header_map["directories"]))  # upper_level leads backwards
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent)
            upper_level.setText(1, "UpOneLevel")
            upper_level.setIcon(0, icon)
            self.addTopLevelItem(upper_level)
            skip_files = len(header_map["directories"][str(goto_dir)]["files"]) == 0

        # Files second which exist in goto_path
        if not skip_files:
            for entry in header_map["files"].values():
                if entry["path"] == goto_dir:
                    file = File(entry)
                    item = CustomQTreeWidgetItem([file.get_metadata()["name"]])
                    icon_bytes = get_file_from_vault(vault_path,file.get_metadata()["icon_data_start"],file.get_metadata()["icon_data_end"])
                    icon = extract_icon_from_bytes(icon_bytes)
                    item.set_path(file.get_path()) # the file item must point to where it is.
                    item.setIcon(0, icon)
                    item.set_saved_obj(file)
                    self.set_item_text(item, file)
                    self.addTopLevelItem(item)

        self.resize_columns(50)
        self.setCurrentItem(self.topLevelItem(0))
        return True

    def resize_columns(self, extra_pixels : int = 0) -> None:
        """Resizes the columns to fit the data nicely with a little extra space
        """
        for i in range(self.columnCount()):
            width = self.columnWidth(i)
            content_width = self.sizeHintForColumn(i)
            if content_width > width:
                self.setColumnWidth(i, content_width + extra_pixels)

    def set_item_text(self, item: CustomQTreeWidgetItem, entry) -> None:
        """
        Set text and icons for each item in the tree widget based on file information.

        Args:
            item (CustomQTreeWidgetItem): The item to set text and icons for.
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
        else:
            for i in range(1, self.columnCount()):
                if i == 2 and item.text(1) == "Folder":
                    continue
                else:
                    item.setText(i, text_mappings.get(i, ""))

    def handle_double_clicked(self, item: CustomQTreeWidgetItem) -> None:
        """
        Handle double-click events on tree widget items.

        Args:
            item (CustomQTreeWidgetItem): The item that was double-clicked.
        """
        if item.text(1) == "Folder" or item.text(1) == "UpOneLevel":
            print(f"Double clicked a folder, '{item.text(0)}', extension: '{item.text(1)}', type: '{type(item.get_saved_obj())}'")
            if self.vaultview:
                self.populate_from_header(header_map=self.__header_map, goto_dir=item.get_path(),vault_path=self.__vaultpath)
                child_path = Directory.determine_directory_path(item.get_path(),self.__header_map["directories"])
                self.updated_signal.emit(child_path)
            else:
                self.populate(item.get_path())
                self.updated_signal.emit(item.get_path())
        else:
            print(f"Double clicked: '{item.text(0)}', extension: '{item.text(1)}', type: '{type(item.get_saved_obj())}'")

    def mousePressEvent(self, event : QMouseEvent) -> None:
        """
        Handle mouse press events, and send a signal to update vault location widget if a file is clicked

        Args:
            event (QMouseEvent): The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
            self.setCurrentItem(self.itemAt(event.pos()))
        super().mousePressEvent(event)
        if self.currentItem() and self.currentItem().text(1) not in ["Folder", "UpOneLevel"]:
            self.clicked_file_signal.emit(self.currentItem().get_path())

    def keyPressEvent(self, event : QKeyEvent):
        """Handle Enter Key and Backspace Key press

        Args:
            event (QKeyEvent): Enter Key clicked
        """
        if event.key() == Qt.Key.Key_Return and self.currentItem():
            if self.currentItem().text(1) in ("Folder", "UpOneLevel"):
                if self.vaultview:
                    self.populate_from_header(header_map=self.__header_map, goto_dir=self.currentItem().get_path(),vault_path=self.__vaultpath)
                    the_goto_path = Directory.determine_directory_path(self.currentItem().get_path(),self.__header_map["directories"])
                    self.updated_signal.emit(the_goto_path)
                else:
                    self.populate(self.currentItem().get_path())
                    self.updated_signal.emit(self.currentItem().get_path())
            else:
                self.clicked_file_signal.emit(self.currentItem().get_path())
        elif event.key() == Qt.Key.Key_Backspace:
            first_item = self.topLevelItem(0)
            if first_item and first_item.text(0) == "..":
                self.setCurrentItem(first_item)
                the_goto_path = first_item.get_path()
                if self.vaultview:
                    self.populate_from_header(header_map=self.__header_map, goto_dir=the_goto_path,vault_path=self.__vaultpath)
                    parent_path = Directory.determine_directory_path(first_item.get_path(),self.__header_map["directories"])
                    self.updated_signal.emit(parent_path)
                else:
                    self.populate(the_goto_path)
                    self.updated_signal.emit(the_goto_path)
        else:
            super().keyPressEvent(event)
