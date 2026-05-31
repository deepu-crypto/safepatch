"""
user_service.py

This file simulates a small user profile service.

Intentional issue:
- get_user_profile() does not properly restrict admin-only profile access.
"""

USER_PROFILES = {
    1: {
        "id": 1,
        "name": "Deepthi",
        "email": "deepthisree1012@gmail.com",
        "salary_visible": False
    },
    2: {
        "id": 2,
        "name": "Admin User",
        "email": "admin@example.com",
        "salary_visible": True
    }
}


def get_user_profile(user_id, requesting_user_role):
    """
    Returns user profile.

    Intentional security issue:
    Any role can request any user profile.
    A real system should check whether the requester is admin
    or whether the requester owns the profile.
    """

    profile = USER_PROFILES.get(user_id)

    if profile is None:
        return {
            "status": 404,
            "message": "User not found"
        }

    return {
        "status": 200,
        "profile": profile
    }