import pytest
from custom_exceptions.utils_exceptions import ClashedIdException, MagicFailure

def test_ClashedIdException():
    with pytest.raises(ClashedIdException) as exc_info:
        raise ClashedIdException("Clashed ID detected")
    assert str(exc_info.value) == "Clashed ID(s) detected during conversion from list to set. Clashed ID detected"

def test_MagicFailure():
    with pytest.raises(MagicFailure) as exc_info:
        raise MagicFailure("Failed to find magic bytes")
    assert str(exc_info.value) == "MagicFailure: Failed to find magic bytes"
