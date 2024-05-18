class LogSession:
    """Class to hold logs generated during runtime"""

    def __init__(self):
        self.__normal_logs = ""
        self.__error_logs = ""

    def add_normal_log(self, log: str):
        """Adds a normal log and a newline character

        Args:
            log (str): log generated by the Logger
        """
        self.__normal_logs += log + "\n"

    def get_normal_logs(self) -> str:
        """Gets the WARN and INFO logs

        Returns:
            str: Returns all the normal logs concatenated with a newline
        """
        return self.__normal_logs

    def add_error_log(self, log: str):
        """Adds an error log and a newline character

        Args:
            log (str): log generated by the Logger
        """
        self.__error_logs += log + "\n"

    def get_error_logs(self) -> str:
        """Gets the ERROR logs

        Returns:
            str: Returns all the error logs concatenated with a newline
        """
        return self.__error_logs
