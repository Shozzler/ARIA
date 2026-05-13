"""
Authentication module for ARIA
Handles user login, password hashing, and session management
"""

import json                    # For reading/writing user data to files
import os                      # For working with file paths
import logging                 # For printing helpful messages
from werkzeug.security import generate_password_hash, check_password_hash
# For secure password storage

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:

    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:

    return check_password_hash(password_hash, password)

def ensure_data_folder():
        """Create the data folder if it doesn't exist"""
        os.makedirs("data", exist_ok=True)
        logger.info("Data folder is ready")


class User:
    """
    Represents a user in the ARIA system.
    Stores username, password hash, and user data.
    """
    
    def __init__(self, username: str, password: str):
        """
        Create a new user.
        username: the login username
        password: the plain password (will be hashed)
        """
        self.username = username
        self.password_hash = hash_password(password)
        self.is_authenticated = False
    
    def verify_password(self, password: str) -> bool:
        """
        Check if provided password matches the stored hash.
        """
        return verify_password(password, self.password_hash)
    
    def to_dict(self) -> dict:
        """
        Convert user to a dictionary (for storing in file).
        """
        return {
            "username": self.username,
            "password_hash": self.password_hash
        }

# File path for storing users
USERS_FILE = os.path.join("data", "users.json")

