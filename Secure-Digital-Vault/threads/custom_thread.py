from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer


class Worker(QObject):
    finished = pyqtSignal(object)
    progress = pyqtSignal(object)
    interaction = pyqtSignal(object)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result = self.function(*self.args, **self.kwargs)
        self.finished.emit(result)


class CustomThread(QThread):
    """Thread that should run for a certain amount of time

    Args:
        QThread (_type_): CustomThread based on QThread to provide concurrency
    """
    progress = pyqtSignal(int)
    timeout_signal = pyqtSignal(object)

    def __init__(self, allowed_runtime: int = 100, function_name_to_handle : str = None):
        """Constructor for the Thread

        Args:
            allowed_runtime (int, optional): Allowed runtime of thread in seconds. Defaults to 0 (Unlimited) if not specified.
            function_name_to_handle (str, optional): Function name which is going to be handled. Defaults to None.
        """
        super().__init__()
        self.__is_deleted = False # This is modified by deleteLater to mark if the C++ Object is deleted.
        self.timeout = allowed_runtime*1000 # allowed time to run in seconds
        self.handled_function = function_name_to_handle

        # Create a singleshot timer to reach the max allowed runtime
        self.timer_finished = False
        self.timer_singleshot = QTimer(self)
        self.timer_singleshot.setSingleShot(True)
        self.timer_singleshot.timeout.connect(self.handle_timeout)

        # Create a normal timer for emitting a progress signal every ~100ms
        self.timer_normal = QTimer(self)
        self.timer_normal.timeout.connect(self.update_progress)

        if self.timeout != 0:
            self.timer_singleshot.start(self.timeout)
            self.timer_normal.start(allowed_runtime*10) # ~100ms
        else:
            self.timer_normal.start(allowed_runtime*100) # ~1000ms

    def update_progress(self) -> None:
        """Emits a progress signal with the value 1 every (self.timeout*10) milisecond. Approx ~ every 100ms
        """
        if not self.timer_finished:
            self.progress.emit(1)
        else:
            self.handle_timeout(emit_finish=False)


    def handle_timeout(self, emit_finish : bool = True) -> None:
        """When timeout is reached and the worker did not emit a signal, stop the timer and emit finish signal (Ungraceful exit)

        Args:
            emit_finish (bool, optional): if the "finished" signal should be emitted.
        """
        if not self.timer_finished:
            self.__clean_up_timers()
            self.timeout_signal.emit("Not Found")
            self.progress.emit(100)
        if emit_finish:
            self.finished.emit()
        self.requestInterruption()


    def stop_timer(self, emit_finish: bool = True, emitted_result : object = None) -> None:
        """When timeout is not reached and the worker emitted a signal, stop the timer and emit finish signal (Graceful exit)

        Args:
            emitted_result (object, optional): Defaults to None.
            emit_finish (bool, optional): if the "finished" signal should be emitted.
        """
        if not self.timer_finished:
            self.__clean_up_timers()
            if emitted_result is None:
                self.timeout_signal.emit("Not Found")
            else:
                self.timeout_signal.emit(emitted_result)
            self.progress.emit(100)
        if emit_finish:
            self.finished.emit()
        self.requestInterruption()

    def __clean_up_timers(self) -> None:
        """Cleans up the timers by stopping them, and then deleting them. This is done automatically
        """
        if not self.timer_finished:
            try:
                self.timer_normal.stop()
                self.timer_normal.deleteLater()
            except RuntimeError:
                pass    # wrapped C/C++ object of type CustomThread has been deleted
            try:
                self.timer_singleshot.stop()
                self.timer_singleshot.deleteLater()
            except RuntimeError:
                pass # wrapped C/C++ object of type CustomThread has been deleted
            self.timer_finished = True

    def deleteLater(self):
        """Deletes the thread and any important items inside it.
        """
        self.__clean_up_timers()
        super().deleteLater()

    def exit(self) -> None:
        try:
            super().exit()
        except RuntimeError:
            pass # wrapped C/C++ object of type CustomThread has been deleted
        if not self.timer_finished:
            self.stop_timer(emit_finish=False)
