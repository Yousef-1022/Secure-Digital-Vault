import threading
import datetime
import time
from PyQt6.QtCore import pyqtSignal
from logger.log_session import LogSession

class Logger:
    """A Logger of a Singleton type pattern"""
    _instance = None
    __lock = threading.Lock()

    def __new__(cls, error_signal : pyqtSignal = None, warn_signal : pyqtSignal = None):
        if cls._instance is None:
            with cls.__lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super().__new__(cls)
                    cls._instance.__initialize(error_signal, warn_signal)
        return cls._instance

    def __initialize(self, error_signal : pyqtSignal = None, warn_signal : pyqtSignal = None):
        self.__log_session = LogSession()
        if error_signal:
            self.error_signal = error_signal
        if warn_signal:
            self.warn_signal = warn_signal

    def info(self, log_message: str):
        """Sends an INFO log

        Args:
            log_message (str): The INFO log
        """
        self.__log("INFO", log_message)

    def warn(self, log_message: str, source="normal_logs"):
        """Sends a WARN log, if warn_signal exists, then emits the log as well

        Args:
            log_message (str): The WARN log
        """
        if source == "normal_logs":
            self.__log("WARNING", log_message)
        else:
            self.__log("WARNING", log_message, is_error=True)
        if self.warn_signal:
            self.warn_signal.emit(log_message)

    def error(self, log_message: str):
        """Sends an ERROR log, if error_signal exists, then emits the log as well

        Args:
            log_message (str): The ERROR log
        """
        self.__log("ERROR", log_message, is_error=True)
        if self.error_signal:
            self.error_signal.emit(log_message)

    def attention(self, log_message:str) -> str:
        """Generates an ATTENTION log but does not add it into the session

        Args:
            log_message (str): The ATTENTION log

        Returns:
            str: The ATTENTION log
        """
        return self.__log("ATTENTION", log_message, is_error=False, no_session=True)

    def __log(self, level:str, log_message:str, is_error:bool=False, no_session=False):
        """Main logging function

        Args:
            level (str): level of the log
            log_message (str): the message
            is_error (bool, optional): type of log whether its ERROR or anything else. Defaults to False.
            no_session (bool, optional): if True, then it only returns the log message. Defaults to False.

        Returns:
            _type_(str): Incase of no_session, it returns the generated log
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} [{level}]: Message: {log_message}"
        try:
            with self.__lock:
                if no_session:
                    return log_message
                if is_error:
                    self.__log_session.add_error_log(log_message)
                else:
                    self.__log_session.add_normal_log(log_message)
        except Exception as e:
            msg = f"{log_message} - FAILED_LOCK_ACQUISITION_EXCEPTION: {type(e).__name__} with message: {str(e)}"
            self.__log_session.add_error_log(msg)

    def get_all_normal_logs(self) -> str:
        """Returns all the normal logs created

        Returns:
            str: The normal logs
        """
        return self.__log_session.get_normal_logs()

    def get_all_error_logs(self) -> str:
        """Returns all the error logs created

        Returns:
            str: The error logs
        """
        return self.__log_session.get_error_logs()

    @staticmethod
    def get_current_time() -> int:
        """Gets the current time

        Returns:
            int: Returns the current time
        """
        return int(time.time())

    @staticmethod
    def form_log_message(msg : str, level : str = "ATTENTION") -> str:
        """Forms a log message which is not added to the session

        Args:
            msg (str): message of the log
            level (str, optional): log level. Defaults to "ATTENTION".

        Returns:
            str: The log message
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} [{level}]: Message: {msg}"

    @classmethod
    def delete_instance(cls):
        """Deletes the running logger
        """
        with cls.__lock:
            if cls._instance is not None:
                cls._instance = None
