from gui.Browser import VaultSearchWindow
from gui.VaultView import VaultViewWindow
from gui.custom_widgets.view_file_window import ViewFileWindow
from PyQt6 import QtWidgets
import sys

from utils.extractors import find_magic, get_file_from_vault, get_icon_from_file
from utils.constants import MAGIC_HEADER_START , MAGIC_HEADER_END, MAGIC_FOOTER_START, MAGIC_FOOTER_END

app = QtWidgets.QApplication(sys.argv)


header_start = find_magic("Vault.yousef", MAGIC_HEADER_START.encode())
header_end =   find_magic("Vault.yousef", MAGIC_HEADER_END.encode())
header = get_file_from_vault("Vault.yousef", header_start, header_end-len(MAGIC_HEADER_END))

# footer_start = find_magic("Vault", MAGIC_FOOTER_START.encode(),-1,True)
# footer_end =   find_magic("Vault", MAGIC_FOOTER_END.encode(),-1,True)
# print(f"Start: {footer_start} , End: {footer_end}")
# header = get_file_from_vault("Vault", footer_start, footer_end-len(MAGIC_HEADER_END))



MainWindow = VaultViewWindow(header, "Vault.yousef")
#MainWindow = VaultSearchWindow()
#MainWindow = ViewFileWindow()

MainWindow.show()
sys.exit(app.exec())
