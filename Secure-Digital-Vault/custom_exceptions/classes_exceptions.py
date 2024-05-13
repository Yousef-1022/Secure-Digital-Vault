

class FileDoesNotExist(Exception):
    """Exception when trying to look up for a file but it does not exist"""
    def __init__(self, message):
        self.message = f"FileDoesNotExist exception raised. {message}"
        super().__init__(self.message)

class JsonWithInvalidData(Exception):
    """Exception when a certain JSON (header,map) has invalid data inside"""
    def __init__(self, message):
        self.message = f"JsonWithInvalidData: {message}"
        super().__init__(self.message)

class MissingKeyInJson(Exception):
    """Exception when a certain JSON (header,map) has a missing mandatory key inside"""
    def __init__(self, message):
        self.message = f"MissingKeyInJson: {message}"
        super().__init__(self.message)

class InvalidMetaData(Exception):
    """Exception when MetaData has a missing mandatory key inside. Used in File lookup / directory Lookup"""
    def __init__(self, message):
        self.message = f"InvalidMetaData: {message}"
        super().__init__(self.message)

class FileError(Exception):
    """Exception when something went wrong with a file"""
    def __init__(self, message):
        self.message = f"FileError: {message}"
        super().__init__(self.message)

class DecryptionFailure(Exception):
    """Exception when couldn't decrypt something"""
    def __init__(self, message):
        self.message = f"DecryptionFailure: {message}"
        super().__init__(self.message)

