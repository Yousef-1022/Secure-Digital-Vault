import pytest
from crypto.encryptors import encrypt_bytes, generate_password_token
from crypto.decryptors import decrypt_bytes, resolve_token
from custom_exceptions.classes_exceptions import DecryptionFailure

@pytest.fixture
def sample_data():
    data = b'Secure-Digital-Vault:SOME_BLOCKS'
    password = 'password123'
    return data, password

def test_decrypt_bytes(sample_data):
    data, password = sample_data
    encrypted_data = encrypt_bytes(data, password)
    decrypted_data = decrypt_bytes(encrypted_data, password)
    assert decrypted_data == data

def test_resolve_token(sample_data):
    data, password = sample_data
    token = generate_password_token(password)
    resolved_token = resolve_token(token)
    assert resolved_token == password

def test_decrypt_bytes_failure():
    encrypted_data = b'\x00\x01\x02\x03\x04'
    password = 'password123'
    with pytest.raises(DecryptionFailure):
        decrypt_bytes(encrypted_data, password)

