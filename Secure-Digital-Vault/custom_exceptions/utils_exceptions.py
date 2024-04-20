"""
utils_exceptions.py

Defines custom exceptions which may arise because of any functions from the util module.
"""


class ClashedIdException(Exception):
    """Exception when converting from a list of IDs to a set of IDs causes a loss in one of IDs which means there are two files with similar IDs"""
    def __init__(self, message):
        self.message = f"Clashed ID(s) detected during conversion from list to set. {message}"
        super().__init__(self.message)

class MagicFailure(Exception):
    """Exception when trying to find certain Magic bytes"""
    def __init__(self, message):
        self.message = f"MagicFailure: {message}"
        super().__init__(self.message)