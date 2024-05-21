import pytest
from file_handle.file_io import *
from utils.constants import *
from config import BASE_DIR
import os

@pytest.fixture
def sample_vault():
    vault_path= f'{BASE_DIR}\\tests\\file_handle\\tester.tester'
    vault_password = 'Tester@123'
    vault_tokens = [
        "jXFdmesvYAGTcMbZvDM4Z1NDFOUXWbDdjE+leEw2smVfuI+jtuR88RUx/g1FYUzw",
        "rltJdBO80qJDjUpwNHBppARfzkbsIEvnDa4/N5bipZxrtk1pP67xJTEoupgWrwF/",
        "geC41wVlyOpGVieVQdNcGD3Bc485vh8y6N1jmgJeWBVMEXf37ftFTzeD8SV2aeoh"
    ]
    return vault_path, vault_password, vault_tokens

def test_find_magic(sample_vault):
    vault_path,vault_password,vault_tokens = sample_vault
    a = xor_magic(MAGIC_HEADER_PAD)
    result = find_magic(vault_path, a)
    assert result == 352

def test_header_points(sample_vault):
    vault_path,vault_password,vault_tokens = sample_vault
    assert [4096, 336, 0, 344, 4448] == find_header_pointers(vault_path)

def test_add_magic_into_header():
    invalid_header = b'suresixteenbytes'
    magic_block = add_magic_into_header(invalid_header)
    assert len(magic_block) == 40

def test_add_magic_into_footer():
    invalid_footer = b'suresixteenbytes'
    magic_block = add_magic_into_footer(invalid_footer)
    assert len(magic_block) == 32

def test_remove_bytes_from_ending_of_file():
    f_name = "test_remove_bytes_from_ending_of_file"
    with open(f_name, 'wb') as f:
        f.write(b'suresixteenbytes')
    res = remove_bytes_from_ending_of_file(f_name, 6)
    assert res == 10
    os.remove(f_name)

def test_append_bytes_into_file():
    f_name = "test_append_bytes_into_file"
    with open(f_name, 'wb') as f:
        f.write(b'suresixteenbytes')
    res = append_bytes_into_file(f_name, b'ten_bytes!')
    assert res == (True, '', 16, 26)
    os.remove(f_name)

def test_stabilize_after_failed_append():
    f_name = "stabilize_after_failed_append"
    with open(f_name, 'wb') as f:
        f.write(b'suresixteenbytes')
    res = stabilize_after_failed_append(f_name, "Appending Failure. appended: 10", 16)
    block = b''
    with open(f_name, 'rb') as f:
        block = f.read()
    assert b'suresi' == block
    assert res == "Appending Failure. appended: 10, Size is: '10', removal of appended 10 bytes makes new vault size: 6 while the old size was: 16"
    os.remove(f_name)

def test_override_bytes_in_file_no_push_default():
    f_name = "test_override_bytes_in_file_no_push"
    with open(f_name, 'wb') as f:
        f.write(b'suresixteenbytes')
    fd = override_bytes_in_file(file_path=f_name, given_bytes=b'surekikteenbytes', byte_loss=0)
    if not fd:
        fd = open(f_name, 'rb')
    fd.seek(0,0)
    data = fd.read()
    fd.close()
    assert data == b'surekikteenbytes'
    os.remove(f_name)

def test_override_bytes_in_file_no_push():
    f_name = "test_override_bytes_in_file_no_push"
    with open(f_name, 'wb') as f:
        f.write(b'test123')
    fd = override_bytes_in_file(file_path=f_name, given_bytes=b'hey', byte_loss=0, at_location=3)
    if not fd:
        fd = open(f_name, 'rb')
    fd.seek(0,0)
    data = fd.read()
    fd.close()
    assert data == b'teshey3'
    os.remove(f_name)

def test_override_bytes_in_file_push_exact_chunk():
    f_name = "test_override_bytes_in_file_push_exact_chunk"
    original_word = b'suresixteenbytes'
    with open(f_name, 'wb+') as f:
        f.write(original_word)
        f.seek(0,0)
    to_add = b'ten_bytes!'
    fd = override_bytes_in_file(file_path=f_name, given_bytes=to_add, byte_loss=len(to_add), at_location=4, chunk_size=len(to_add))
    if not fd:
        fd = open(f_name, 'rb')
    fd.seek(0,0)
    data = fd.read()
    fd.close()
    assert data == b'sureten_bytes!sixteenbytes'
    os.remove(f_name)

def test_override_bytes_in_file_push_default_chunk():
    f_name = "test_override_bytes_in_file_push_default_chunk"
    original_word = b'some__bytes_here'
    with open(f_name, 'wb+') as f:
        f.write(original_word)
        f.seek(0,0)
    to_add = b'ten_bytes!'
    fd = override_bytes_in_file(file_path=f_name, given_bytes=to_add, byte_loss=len(to_add), at_location=5)
    if not fd:
        fd = open(f_name, 'rb')
    fd.seek(0,0)
    data = fd.read()
    fd.close()
    assert data == b'some_ten_bytes!_bytes_heree'
    os.remove(f_name)

def test_delete_footer_and_hint(sample_vault):
    vault_path,vault_password,vault_tokens = sample_vault
    original = None
    with open (vault_path, "rb") as f:
        original = f.read()
    loc_start = find_magic(vault_path, xor_magic(MAGIC_LOG_START))
    delete_footer_and_hint(vault_path, loc_start)
    deleted = loc_start - 8
    assert get_file_size(vault_path) == deleted
    with open(vault_path, "wb") as f:
        f.write(original)

def test_get_hint(sample_vault):
    vault_path,vault_password,vault_tokens = sample_vault
    assert get_hint(vault_path) == "TestHint"
