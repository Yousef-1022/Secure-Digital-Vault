from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer

class Worker(QObject):
    finished = pyqtSignal(object)
    progress = pyqtSignal(object)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        print("Worker began")
        result = self.function(*self.args, **self.kwargs)
        self.finished.emit(result)
        print("Worker ended")


class CustomThread(QThread):
    """Thread that should run for a certain amount of time

    Args:
        QThread (_type_): CustomThread based on QThread to provide concurrency
    """
    progress = pyqtSignal(int)
    timeout_signal = pyqtSignal(object)

    def __init__(self, allowed_runtime: int = 0, function_name_to_handle : str = None):
        """Constructor for the Thread

        Args:
            allowed_runtime (int, optional): Allowed runtime of thread in seconds. Defaults to 0 (Unlimited) if not specified.
            function_name_to_handle (str, optional): Function name which is going to be handled. Defaults to None.
        """
        super().__init__()
        self.timeout = allowed_runtime*1000 # allowed time to run in seconds
        self.handled_function = function_name_to_handle

        self.timer_finished = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.handle_timeout)
        self.timer.start(self.timeout)

    def handle_timeout(self) -> None:
        """When timeout is reached and the worker did not emit a signal, stop the timer and emit finish signal (Ungraceful exit)
        """
        print("handle_timeout called (ungraceful)")
        if(not self.timer_finished):
            self.timer_finished = True
            self.timer.stop()
            self.timeout_signal.emit("Not Found")
            self.timer.deleteLater()
        self.finished.emit()
        self.requestInterruption()


    def stop_timer(self, emitted_result : object = None) -> None:
        """When timeout is not reached and the worker emitted a signal, stop the timer and emit finish signal (Graceful exit)

        Args:
            emitted_result (object, optional): _description_. Defaults to None.
        """
        print("stop_timer called (graceful)",object)
        if(not self.timer_finished):
            self.timer_finished = True
            self.timer.stop()
            self.timer.deleteLater()
            if emitted_result is None:
                self.timeout_signal.emit("Not Found")
            else:
                self.timeout_signal.emit(emitted_result)
        self.finished.emit()
        self.requestInterruption()

