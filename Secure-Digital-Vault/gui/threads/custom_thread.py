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
        self.timer.singleShot(self.timeout,self.handle_timeout)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(allowed_runtime*10)   # Used for emitting a progress signal every ~100ms


    def update_progress(self) -> None:
        """Emits a progress signal with the value 1 every (self.timeout*10) milisecond. Approx ~ every 100ms
        """
        if not self.timer_finished:
            self.progress.emit(1)
        else:
            self.handle_timeout()


    def handle_timeout(self) -> None:
        """When timeout is reached and the worker did not emit a signal, stop the timer and emit finish signal (Ungraceful exit)
        """
        print(f"handle_timeout called (ungraceful). timer_finished: {self.timer_finished}")
        if(not self.timer_finished):
            self.timer_finished = True
            self.timer.stop()
            self.timeout_signal.emit("Not Found")
            self.timer.deleteLater()
            self.progress.emit(100)
        self.finished.emit()
        self.requestInterruption()


    def stop_timer(self, emitted_result : object = None) -> None:
        """When timeout is not reached and the worker emitted a signal, stop the timer and emit finish signal (Graceful exit)

        Args:
            emitted_result (object, optional): _description_. Defaults to None.
        """
        print(f"stop_timer called (graceful). timer_finished: {self.timer_finished}")
        if(not self.timer_finished):
            self.timer_finished = True
            self.timer.stop()
            self.timer.deleteLater()
            if emitted_result is None:
                self.timeout_signal.emit("Not Found")
            else:
                self.timeout_signal.emit(emitted_result)
            self.progress.emit(100)
        self.finished.emit()
        self.requestInterruption()

