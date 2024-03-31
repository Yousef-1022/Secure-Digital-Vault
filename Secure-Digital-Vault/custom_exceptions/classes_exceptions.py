"""
classes_exceptions.py

Defines custom exceptions which may arise because of any functions from the classes module.
"""


class FileDoesNotExist(Exception):
    """Exception when trying to look up for a file but it does not exist"""
    def __init__(self, message):
        self.message = f"FileDoesNotExist exception raised. {message}"
        super().__init__(self.message)


class JsonWithInvalidData(Exception):
    """Exception when a certain JSON (header,footer,map) has invalid data inside"""
    def __init__(self, message):
        self.message = f"JsonWithInvalidData exception raised. {message}"
        super().__init__(self.message)


class MissingKeyInJson(Exception):
    """Exception when a certain JSON (header,footer,map) has a missing mandatory key inside"""
    def __init__(self, message):
        self.message = f"MissingKeyInJson exception raised. {message}"
        super().__init__(self.message)


class InvalidMetaData(Exception):
    """Exception when MetaData has a missing mandatory key inside. Used in File lookup / directory Lookup"""
    def __init__(self, message):
        self.message = f"InvalidMetaData exception raised. {message}"
        super().__init__(self.message)

