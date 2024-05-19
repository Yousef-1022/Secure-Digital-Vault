import struct, hashlib, base64

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from utils.constants import CHUNK_LIMIT


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

def get_checksum(data : object, is_file : bool, divide_by : int = 4) -> str:
    """
    Calculate the SHA-256 checksum of either a block of data or a file.

    Args:
        data (bytes): The data to calculate the checksum for, either a filepath or block of data
        is_file (bool): If its a file path
        divide_by (int) optional: 4 by default, return the checksum divided by this num. It cannot be larger than 32

    Returns:
        str: The hexadecimal representation of the SHA-256 checksum, length is dependent on divide_by argument
    """
    sha256 = hashlib.sha256()
    if divide_by > 32:
        divide_by = 4

    if not is_file:
        sha256.update(data)
        checksum = sha256.hexdigest()
        return checksum[:int(len(checksum)/divide_by)]

    with open(data, 'rb') as f:
        for chunk in iter(lambda: f.read(CHUNK_LIMIT), b''):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    return checksum[:int(len(checksum)/divide_by)]

def calc_easy_checksum(data):
    """Calculate the checksum for some block of data.
    incase length is not a multiple of four, then assumption is that it is to be padded with null byte.
    """
    rmndr = len(data) % 4
    if rmndr:
        data += b"\0" * (4 - rmndr)
    value = 0
    block_size = 4096
    assert block_size % 4 == 0
    for i in range(0, len(data), block_size):
        block = data[i : i + block_size]
        lngs = struct.unpack(">%dL" % (len(block) // 4), block)
        value = (value + sum(lngs)) & 0xFFFFFFFF
    return value

def generate_aes_key(password : str, salt : bytes, key_length : int) -> bytes:
    """
    Generate an AES key from a password using PBKDF2.

    Args:
        password (str): The password to derive the key from.
        salt (bytes): The salt to use in key derivation.
        key_length (int): The length of the derived key in bytes.

    Returns:
        bytes: The derived AES key.
    """
    return PBKDF2(password=password, salt=salt, dkLen=key_length)

def calculate_encrypted_chunk_size(given_size: int) -> int:
    """Calculates the exact encrypted chunk size

    Args:
        given_size (int): The size of the encrypted chunk

    Summary:
        Calculates the number of padding bytes to get the total encrypted size.
        Total encrypted size = given_size + padding size + IV + Salt

    Returns:
        int: given_size+encryption_overhead
    """
    block_size = AES.block_size
    padding_size = block_size - (given_size % block_size)
    overhead = padding_size + 16 + 16
    return given_size + overhead

def to_base64(some_bytes: bytes) -> str:
    """
    Convert bytes to Base64 encoded string.

    Args:
        some_bytes (bytes): The bytes to encode.

    Returns:
        str: The Base64 encoded string.
    """
    base64_str = base64.b64encode(some_bytes)
    base64_str = base64_str.decode('utf-8')
    return base64_str

def from_base64(base64_str: str) -> bytes:
    """
    Convert Base64 encoded string back to bytes.

    Args:
        base64_str (str): The Base64 encoded string.

    Returns:
        bytes: The decoded bytes.
    """
    base64_bytes = base64_str.encode('utf-8')
    original_bytes = base64.b64decode(base64_bytes)
    return original_bytes
