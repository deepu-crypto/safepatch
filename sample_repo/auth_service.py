"""
auth_service.py

This file simulates a small authentication service.

Intentional bug:
- login() crashes when email is missing because email.lower() is called without validation.
"""

USERS = {
    "deepthisree1012@gmail.com": {
        "password": "password123",
        "role": "user"
    },
    "admin@example.com": {
        "password": "admin123",
        "role": "admin"
    }
}


def login(email, password):
    """
    Login a user using email and password.

    Bug:
    If email is None, this line crashes:
    normalized_email = email.lower()
    """

    normalized_email = email.lower()

    user = USERS.get(normalized_email)

    if user is None:
        return {
            "status": 401,
            "message": "Invalid email or password"
        }

    if user["password"] != password:
        return {
            "status": 401,
            "message": "Invalid email or password"
        }

    return {
        "status": 200,
        "message": "Login successful",
        "token": "fake-jwt-token",
        "role": user["role"]
    }


def reset_password(email):
    """
    Simulates password reset.

    Intentional weakness:
    The reset token is static and does not expire.
    """

    if email not in USERS:
        return {
            "status": 404,
            "message": "User not found"
        }

    return {
        "status": 200,
        "reset_token": "static-reset-token"
    }