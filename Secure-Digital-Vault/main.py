from PyQt6.QtWidgets import QApplication
from gui.ViewManager import ViewManager

import sys

sys.argv += ['-platform', 'windows:darkmode=1'] # 1 = light Theme
app = QApplication(sys.argv)
app.setStyle("Fusion")
MainWindow = ViewManager()
MainWindow.show()
sys.exit(app.exec())
