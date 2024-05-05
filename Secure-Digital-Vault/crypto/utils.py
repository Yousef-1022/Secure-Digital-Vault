

def is_password_strong(password : str) -> tuple[bool,list[str]]:
    """Checks whether the given password meets security standards:
    Length >= 6 , Upper Char, Lower Char, a Digit, Special Char

    Args:
        password (str): Given Password

    Returns:
        tuple[bool,list[str]]: First part is a boolean value if its strong, Second part is the list of strings indicating what is wrong.
    """
    reasons = []

    if len(password) < 6:
        reasons.append("Password length should be at least 6 characters")

    if not any(char.isupper() for char in password):
        reasons.append("Password should contain at least one uppercase letter")

    if not any(char.islower() for char in password):
        reasons.append("Password should contain at least one lowercase letter")

    if not any(char.isdigit() for char in password):
        reasons.append("Password should contain at least one digit")

    if not any(char in "!@#$%^&*()-_=+[]{}|;:',.<>?`~" for char in password):
        reasons.append("Password should contain at least one special character")

    strong_password = len(reasons) == 0

    return strong_password, reasons

def xor_magic (magic : str) -> bytes:
    """Xors the magic bytes with a special xor key

    Args:
        magic (str): Magic Bytes

    Returns:
        bytes: Xored magic Bytes
    """
    xor_key = [70, 114, 101, 115, 104, 49]
    xored_bytes = bytes([char ^ xor_key[i % len(xor_key)] for i, char in enumerate(magic.encode())])
    return xored_bytes

def get_checksum (file_path : str) -> str:
    """Gets the checksum of the file

    Args:
        file_path (str): Original file location

    Returns:
        str: The check sum
    """
    # TODO: Add checksum
    return "aCheckSum"
