"""Unit tests for password hashing + JWT (app/core/security.py)."""

import uuid

import pytest
from jwt import InvalidTokenError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_roundtrip() -> None:
    hashed = hash_password("Sup3rSecret")
    assert hashed != "Sup3rSecret"
    assert verify_password("Sup3rSecret", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "admin", token_version=0)
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "admin"
    assert payload["token_version"] == 0


def test_refresh_token_rejected_as_access_token() -> None:
    user_id = uuid.uuid4()
    token = create_refresh_token(user_id, "admin", token_version=0)
    with pytest.raises(InvalidTokenError):
        decode_token(token, expected_type="access")
