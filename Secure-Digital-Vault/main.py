import sys
from PyQt6.QtWidgets import QApplication
from gui.ViewManager import ViewManager
from utils import images_qrc

def run():
    sys.argv += ['-platform', 'windows:darkmode=1']  # 1 = light theme
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    MainWindow = ViewManager()
    MainWindow.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()
