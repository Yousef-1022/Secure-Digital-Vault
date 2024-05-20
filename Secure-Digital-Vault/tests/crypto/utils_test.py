import pytest
from crypto.utils import is_password_strong, xor_magic, get_checksum, calc_easy_checksum, generate_aes_key, calculate_encrypted_chunk_size, to_base64, from_base64
from utils.helpers import count_digits

@pytest.fixture
def sample_password():
    return 'StrongPassword123'

def test_is_password_weak(sample_password):
    strong, reasons = is_password_strong(sample_password)
    assert strong == False
    assert len(reasons) == 1

def test_is_password_strong(sample_password):
    strong, reasons = is_password_strong(sample_password)
    assert strong == False
    assert len(reasons) == 1
    strong, reasons = is_password_strong(sample_password+'@')
    assert strong == True
    assert len(reasons) == 0

def test_xor_magic():
    magic = 'SomeMagic'
    xored_magic = xor_magic(magic)
    assert xored_magic is not None
    assert len(xored_magic) == len(magic.encode())

def test_get_checksum():
    data = b'TestData'
    checksum = get_checksum(data, is_file=False)
    assert len (checksum) == 16
    assert checksum == '814d78962b0f8ac2'

def test_calc_easy_checksum():
    data = b'TestData'
    checksum = calc_easy_checksum(data)
    assert count_digits(checksum) == 10
    assert checksum == 2563172309

def test_generate_aes_key(sample_password):
    password = sample_password
    salt = b'SomeSaltSomeSalt'
    key_length = 32
    aes_key = generate_aes_key(password, salt, key_length)
    assert aes_key is not None
    assert len(aes_key) == key_length

def test_calculate_encrypted_chunk_size():
    given_size = 100
    encrypted_chunk_size = calculate_encrypted_chunk_size(given_size)
    assert encrypted_chunk_size is not None

def test_to_base64():
    data = b'TestData'
    base64_str = to_base64(data)
    assert base64_str == 'VGVzdERhdGE='

def test_from_base64():
    base64_str = 'VGVzdERhdGE='
    original_bytes = from_base64(base64_str)
    assert original_bytes == b'TestData'
