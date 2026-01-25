"""Simple no-authentication system.

This module provides a simple no-auth system for development.
All requests are allowed without authentication.
"""


class SimpleUser:
    def __init__(self, user_id: str = "anonymous", email: str = "anonymous@localhost"):
        self.id = user_id
        self.email = email
        self.claims = {"sub": user_id, "email": email}

    def __repr__(self):
        return f"SimpleUser(id={self.id}, email={self.email})"


def get_current_user() -> SimpleUser:
    """Return a simple anonymous user for no-auth development."""
    return SimpleUser()
