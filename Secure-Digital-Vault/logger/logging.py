import threading
import datetime
from logger.log_session import LogSession


class Logger:
    _instance = None
    __lock = threading.Lock()
    __log_session = LogSession()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def info(self, log_message:str):
        self.__log("INFO", log_message)

    def warn(self, log_message:str, source="normal_logs"):
        if source == "normal_logs":
            self.__log("WARNING", log_message)
        else:
            self.__log("WARNING", log_message, is_error=True)

    def error(self, log_message:str):
        self.__log("ERROR", log_message, is_error=True)

    def attention(self, log_message:str) -> str:
        return self.__log("ATTENTION", log_message, is_error=False, no_session=True)

    def __log(self, level:str, log_message:str, is_error:bool=False, no_session=False):
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

    @staticmethod
    def form_log_message(msg : str, level : str = "ATTENTION"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} [{level}]: Message: {msg}"

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

    def get_all_logs(self) -> str:
        """Returns all the logs created

        Returns:
            str: The logs
        """
        return f'Errors:\n{self.__log_session.get_error_logs()}Normal:\n{self.__log_session.get_normal_logs()}'
