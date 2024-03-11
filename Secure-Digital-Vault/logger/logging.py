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

    def __log(self, level:str, log_message:str, is_error:bool=False):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} [{level}]: Message: {log_message}"
        try:
            with self.__lock:
                if is_error:
                    self.__log_session.add_error_log(log_message)
                else:
                    self.__log_session.add_normal_log(log_message)
        except Exception as e:
            msg = f"{log_message}-FAILED_LOCK:{e.message}"
            self.__log_session.add_error_log(msg)
