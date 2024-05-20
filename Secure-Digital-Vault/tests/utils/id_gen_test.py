import pytest
from custom_exceptions.utils_exceptions import ClashedIdException
from utils.id_gen import gen_id

def test_gen_id_empty_list():
    assert gen_id([], "file_ids") == 1

def test_gen_id_no_clashes():
    assert gen_id([1, 2, 3, 4], "file_ids") == 5
    assert gen_id([2, 3, 4], "file_ids") == 1
    assert gen_id([1, 3, 4], "file_ids") == 2

def test_gen_id_with_gaps():
    assert gen_id([1, 3, 4], "file_ids") == 2
    assert gen_id([1, 2, 4, 5], "file_ids") == 3

def test_gen_id_with_clashes():
    with pytest.raises(ClashedIdException) as excinfo:
        gen_id([1, 2, 2, 4], "file_ids")
    assert "file_ids: [2]" in str(excinfo.value)

def test_gen_id_large_values():
    ids = list(range(1, 10000))
    assert gen_id(ids, "file_ids") == 10000

def test_gen_id_near_limit():
    ids = list(range(1, 1000000))
    assert gen_id(ids, "file_ids") == 1000000
