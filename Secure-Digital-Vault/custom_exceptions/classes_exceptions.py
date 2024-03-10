"""
classes_exceptions.py

Defines custom exceptions which may arise because of any functions from the classes module.
"""


class FileDoesNotExist(Exception):
    """Exception when trying to look up for a file but it does not exist"""
    def __init__(self, message):
        self.message = f"FileDoesNotExist exception raised. {message}"
        super().__init__(self.message)
