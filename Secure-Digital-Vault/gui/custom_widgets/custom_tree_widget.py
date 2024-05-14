from PyQt6.QtWidgets import QTreeWidget, QWidget, QFileIconProvider, QStyle, QMessageBox, QApplication
from PyQt6.QtCore import QDir, QFileInfo, Qt , pyqtSignal, QRect, QSize
from PyQt6.QtGui import QMouseEvent , QKeyEvent

from utils.parsers import parse_size_to_string, parse_timestamp_to_string
from utils.extractors import get_file_from_vault, extract_icon_from_bytes
from utils.helpers import get_available_drives
from utils.constants import TREE_COLUMNS, DEFAULT_ICON_SIZE

from classes.file import File
from classes.directory import Directory
from classes.vault import Vault

from gui.custom_widgets.custom_tree_item import CustomQTreeWidgetItem
from gui.custom_widgets.custom_messagebox import CustomMessageBox


class CustomTreeWidget(QTreeWidget):
    """
    Customized QTreeWidget for displaying file system information.

    Parameters:
        columns (int): The number of columns for the tree widget. Default is 4.
        parent (QWidget): The parent widget. Default is None.
    """
    updated_signal = pyqtSignal(object)
    clicked_file_signal = pyqtSignal(object)
    marquee_signal = pyqtSignal()

    def __init__(self, parent: QWidget, vaultview : bool = False , vaultpath : str = None, header_map : dict = None):
        """
        Initialize the custom tree widget.

        Args:
            parent (QWidget): The parent widget.
            vaultview (bool): boolean indicating that the tree widget is meant for VaultView
            vaultpath (str): location of the vault on the disk
            header_map(dict): the header_map dictionary
        """
        super().__init__(parent)

        # data
        self.setIconSize(QSize(DEFAULT_ICON_SIZE, DEFAULT_ICON_SIZE))
        self.vaultview = vaultview
        self.__vaultpath = vaultpath
        self.__header_map = header_map
        self.current_path = 0

        self.headers=None
        self.update_columns_with(TREE_COLUMNS)
        self.itemDoubleClicked.connect(self.handle_double_clicked)

        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.__selection_start_pos = None

    def get_vault_path(self) -> str:
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
        """Updates the tree's columns and column count with the given list

        Args:
            lst (list[str]): List of column headers
        """
        self.headers=lst
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
            message_box = CustomMessageBox(parent=self)
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Unknown location")
            message_box.showMessage(f"Could not find the path {path} on the system!")
            return
        self.clear()
        directory.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDot | QDir.Filter.NoSymLinks)
        file_icon_provider = QFileIconProvider()

        for entry in directory.entryInfoList():
            item = CustomQTreeWidgetItem([entry.fileName()])
            item.setIcon(0, file_icon_provider.icon(entry))
            item.set_path(entry.absoluteFilePath())   # Store file path as an attribute

            # Populate additional columns and add the item directly to the tree widget
            self.set_item_text(item, entry)
            self.addTopLevelItem(item)
        self.update_columns_with(TREE_COLUMNS)
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
        self.current_path = goto_dir

        cleard_once = False # Indicator to clear the tree once, this must be True if the directory is found
        skip_files = False  # Indicator incase the current directory does not have files
        cur_dir_name = Vault.determine_directory_path(path_id=goto_dir, data_dict=header_map["directories"])

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
        self.update_columns_with(TREE_COLUMNS)
        self.setCurrentItem(self.topLevelItem(0))
        return True

    def populate_by_request(self, header_map : dict,  file_dicts : list[dict], vault_path : str) -> bool:
        """Repopulates the tree with the given dicts

        Args:
            header_map (dict): map dict from the header
            file_dicts (list[dict]): The file dicts extracted from the vault
            vault_path (str): The path to the vault

        Returns:
            bool: indicates whether the population was valid
        """
        self.clear()
        if "Location" not in self.headers:
            new_columns = [c for c in self.headers]
            new_columns.append("Location")
            self.update_columns_with(new_columns)
        else:
            self.update_columns_with(self.headers)

        for f in file_dicts:
            file = File(f)
            item = CustomQTreeWidgetItem([file.get_metadata()["name"]])
            icon_bytes = get_file_from_vault(vault_path,file.get_metadata()["icon_data_start"],file.get_metadata()["icon_data_end"])
            icon = extract_icon_from_bytes(icon_bytes)
            item.set_path(file.get_path()) # the file item must point to where it is.
            item.setIcon(0, icon)
            item.set_saved_obj(file)
            item.set_in_vault_location(Vault.determine_directory_path(item.get_path(), header_map["directories"]))
            self.set_item_text(item, file)
            self.addTopLevelItem(item)
        self.setCurrentItem(self.topLevelItem(0))
        self.current_path = 0
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
        Set text and icons for each item in the tree widget based on file information. Default mapping is to length of: TREE_COLUMNS

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
                4: entry.birthTime().toString("dd-MMM-yy HH:mm"),
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
                3: parse_timestamp_to_string(entry.get_last_modified()),
                4: parse_timestamp_to_string(entry.get_data_created())
            }
        if self.columnCount() > 5:
            text_mappings[5] =  item.get_in_vault_location()
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
                child_path = Vault.determine_directory_path(item.get_path(),self.__header_map["directories"])
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
            self.__selection_start_pos = event.pos()
            # If CTRL is clicked
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                item = self.currentItem()
                if item:
                    item.setSelected(not item.isSelected())
        super().mousePressEvent(event)
        if self.currentItem() and self.currentItem().text(1) not in ["Folder", "UpOneLevel"]:
            self.clicked_file_signal.emit(self.currentItem().get_path())

    def setSelectionRect(self, rect: QRect):
        """
        Sets the selection rectangle for items in the tree widget.

        Parameters:
            rect (QRect): The rectangle representing the selection area.
        """
        for item in self.findItems("", Qt.MatchFlag.MatchContains):
            item_rect = self.visualItemRect(item)
            if rect.intersects(item_rect):
                item.setSelected(True)
            else:
                item.setSelected(False)

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Handles mouse move event (LeftButton) to set the selection rectangle.

        Parameters:
            event (QMouseEvent): The mouse event.
        """
        if event.buttons() & Qt.MouseButton.LeftButton:
            if not self.__selection_start_pos:
                self.__selection_start_pos = event.pos()
            rect = QRect(self.__selection_start_pos, event.pos()).normalized()
            self.setSelectionRect(rect)
        super().mouseMoveEvent(event)

    def getSelectedItems(self) -> list[CustomQTreeWidgetItem]:
        """Returns all the selected items by the marquee selection.

        Returns:
            list[CustomQTreeWidgetItem]: List of TreeWidgetItems without the UpOneLevel
        """
        selected = []
        for item in self.selectedItems():
            if item.text(1) != "UpOneLevel":
                selected.append(item)
        return selected

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Handles mouse release events to clear the selection rectangle.

        Parameters:
            event (QMouseEvent): The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.__selection_start_pos = None
            self.marquee_signal.emit()
        super().mouseReleaseEvent(event)

    def selectAllItems(self):
        """
        Selects all items in the tree widget.
        """
        for item in self.findItems("", Qt.MatchFlag.MatchContains):
            item.setSelected(True)

    def keyPressEvent(self, event : QKeyEvent):
        """Handle Enter Key and Backspace Key press

        Args:
            event (QKeyEvent): Enter Key clicked
        """
        if event.key() == Qt.Key.Key_Return and self.currentItem():
            if self.currentItem().text(1) in ("Folder", "UpOneLevel"):
                if self.vaultview:
                    the_goto_path = Vault.determine_directory_path(self.currentItem().get_path(),self.__header_map["directories"])
                    self.populate_from_header(header_map=self.__header_map, goto_dir=self.currentItem().get_path(),vault_path=self.__vaultpath)
                    self.updated_signal.emit(the_goto_path)
                else:
                    go_to = self.currentItem().get_path()
                    self.populate(self.currentItem().get_path())
                    self.updated_signal.emit(go_to)
            else:
                self.clicked_file_signal.emit(self.currentItem().get_path())
        elif event.key() == Qt.Key.Key_Backspace:
            first_item = self.topLevelItem(0)
            if first_item and first_item.text(0) == "..":
                self.setCurrentItem(first_item)
                the_goto_path = first_item.get_path()
                if self.vaultview:
                    self.populate_from_header(header_map=self.__header_map, goto_dir=the_goto_path,vault_path=self.__vaultpath)
                    parent_path = Vault.determine_directory_path(first_item.get_path(),self.__header_map["directories"])
                    self.updated_signal.emit(parent_path)
                else:
                    self.populate(the_goto_path)
                    self.updated_signal.emit(the_goto_path)
        elif event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.selectAllItems()
        else:
            super().keyPressEvent(event)
