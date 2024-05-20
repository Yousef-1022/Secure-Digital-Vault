import pytest
from crypto.encryptors import encrypt_bytes, encrypt_header, encrypt_footer, generate_password_token
from crypto.decryptors import decrypt_bytes, resolve_token

@pytest.fixture
def sample_data():
    data = b'Secure-Digital-Vault:SOME_BLOCKS'
    password = 'password123'
    return data, password

def test_encrypt_bytes(sample_data):
    data, password = sample_data
    encrypted_data = encrypt_bytes(data, password)
    assert encrypted_data is not None
    assert len(encrypted_data) > 0
    answer = decrypt_bytes(encrypted_data, password)
    assert answer == data

def test_encrypt_header():
    password = 'password123'
    header = b'{"vault": {"header_size": 128}, "map": {}}'
    encrypted_header = encrypt_header(password, header)
    assert encrypted_header is not None
    assert len(encrypted_header) > 0

def test_encrypt_footer():
    password = 'password123'
    footer = b'{"error_log": "", "session_log": ""}'
    encrypted_footer = encrypt_footer(password, footer)
    assert encrypted_footer is not None
    assert len(encrypted_footer) > 0
    answer = decrypt_bytes(encrypted_footer, password)
    assert answer == footer

def test_generate_password_token(sample_data):
    data, password = sample_data
    token = generate_password_token(password)
    assert token is not None
    assert len(token) > 0
    encrypted = encrypt_bytes(data, password)
    d1 = decrypt_bytes(encrypted, password)
    d2 = decrypt_bytes(encrypted, resolve_token(token))
    assert d1 == data
    assert d2 == data
