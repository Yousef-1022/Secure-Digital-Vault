from PyQt6.QtWidgets import QProgressBar, QWidget


class CustomProgressBar(QProgressBar):
    def __init__(self, min_value: int = 0, max_value: int = 100, current_value: int = 0, is_visible_at_start: bool = True, parent: QWidget = None):
        """
        Custom progress bar widget.

        Parameters:
            min_value (int, optional): Minimum value of the progress bar.
            max_value (int, optional): Maximum value of the progress bar.
            current_value (int, optional): Initial value of the progress bar.
            is_visible_at_start (bool, optional): Whether the progress bar should be visible initially.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setMinimum(min_value)
        self.setMaximum(max_value)
        self.setValue(current_value)
        self.setVisible(is_visible_at_start)

    def stop_progress(self, hide : bool = True) -> None:
        """
        Stops the progress and hides the progress bar.
        """
        if hide:
            self.setVisible(False)
        self.setValue(0)
