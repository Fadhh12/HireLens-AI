"""Unit tests for the SRS §4 phone validator — regression test for the
"digit count vs total string length" bug found during manual testing."""

import pytest

from app.modules.candidates.schema import validate_phone


@pytest.mark.parametrize(
    "phone",
    [
        "0812345678",  # 10 digits, no formatting
        "+62 813-9988-7766",  # 11 digits, 17 chars with formatting
        "021 555-0100",  # formatted, no parens (SRS §4 doesn't allow "()")
        "12345678",  # exactly 8 digits (lower bound)
        "123456789012345",  # exactly 15 digits (upper bound)
    ],
)
def test_valid_phones_accepted(phone: str) -> None:
    assert validate_phone(phone) == phone


@pytest.mark.parametrize(
    "phone",
    [
        "1234567",  # 7 digits — below minimum
        "1234567890123456",  # 16 digits — above maximum
        "abc12345",  # disallowed characters
        "0812*345678",  # disallowed character (*)
        "(021) 555-0100",  # parens not in SRS §4's allowed charset
    ],
)
def test_invalid_phones_rejected(phone: str) -> None:
    with pytest.raises(ValueError):
        validate_phone(phone)
