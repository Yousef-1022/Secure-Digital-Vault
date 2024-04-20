

def encrypt_header(password : str , header : bytes) -> bytes:
    """Encrypts the header with PLACEHOLDER

    Args:
        password (str): Password.
        header (bytes): Serialized header.

    Returns:
        bytes: Encrypted header.
    """
    return header