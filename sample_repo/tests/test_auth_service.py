"""
test_auth_service.py

This file contains tests for auth_service.py.

One test is expected to fail right now because the bug is intentional.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from auth_service import login


def test_login_success():
    response = login("deepthisree1012@gmail.com", "password123")

    assert response["status"] == 200
    assert response["message"] == "Login successful"


def test_login_missing_email_should_return_400():
    response = login(None, "password123")

    assert response["status"] == 400
    assert response["message"] == "Email is required"
