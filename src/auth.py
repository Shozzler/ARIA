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

def save_user(user: User) -> bool:
    """
    Save a user to the users.json file.
    Takes a User object and saves it.
    Returns True if successful, False if user already exists.
    """
    ensure_data_folder()  # Make sure data folder exists
    
    # Load existing users from file
    users = load_users()  # We'll write this next
    
    # Check if username already exists
    if user.username in users:
        logger.warning(f"User {user.username} already exists")
        return False
    
    # Add new user to the dictionary
    users[user.username] = user.to_dict()
    
    # Save back to file
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file, indent=2)
    
    logger.info(f"User {user.username} saved successfully")
    return True

def load_users() -> dict:
    """
    Load all users from the users.json file.
    Returns a dictionary of users.
    If file doesn't exist, returns empty dictionary.
    """
    ensure_data_folder()  # Make sure folder exists
    
    # Check if users.json file exists
    if not os.path.exists(USERS_FILE):
        logger.info("No users file found, creating new one")
        return {}  # Return empty dictionary
    
    # File exists, so read it
    try:
        with open(USERS_FILE, 'r') as file:
            users = json.load(file)
        logger.info(f"Loaded {len(users)} users from file")
        return users
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {}
    

def login(username: str, password: str) -> bool:
    """
    Authenticate a user with username and password.
    ALSO checks if user is whitelisted.
    Returns True if credentials are correct AND user is whitelisted, False otherwise.
    """
    # Check if user is whitelisted first
    if not is_whitelisted(username):
        logger.warning(f"Login failed: User '{username}' is not whitelisted")
        return False

    # Load all users from file
    users = load_users()

    # Check if username exists
    if username not in users:
        logger.warning(f"Login failed: User '{username}' not found")
        return False

    # Get the user's password hash
    user_data = users[username]
    password_hash = user_data['password_hash']

    # Check if password matches
    if verify_password(password, password_hash):
        logger.info(f"User '{username}' logged in successfully")
        return True
    else:
        logger.warning(f"Login failed: Wrong password for '{username}'")
        return False

class User:
    """
    Represents a user in the ARIA system.
    Stores username, password hash, role, and user data.
    """

    def __init__(self, username: str, password: str, role: str = "user"):
        """
        Create a new user.
        username: the login username
        password: the plain password (will be hashed)
        role: "admin", "user", or "guest" (default: "user")
        """
        self.username = username
        self.password_hash = hash_password(password)
        self.role = role  # admin, user, or guest
        self.is_authenticated = False

    def verify_password(self, password: str) -> bool:
        """
        Check if provided password matches the stored hash.
        """
        return verify_password(password, self.password_hash)

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == "admin"

    def to_dict(self) -> dict:
        """
        Convert user to a dictionary (for storing in file).
        """
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "role": self.role
        }

# File paths
USERS_FILE = os.path.join("data", "users.json")
WHITELIST_FILE = os.path.join("data", "whitelist.json")


def load_whitelist() -> list:
    """
    Load the whitelist of approved usernames.
    Returns a list of approved usernames.
    If file doesn't exist, returns empty list.
    """
    ensure_data_folder()

    if not os.path.exists(WHITELIST_FILE):
        logger.warning("Whitelist file not found")
        return []

    try:
        with open(WHITELIST_FILE, 'r') as file:
            data = json.load(file)
        whitelist = data.get('whitelist', [])
        logger.info(f"Loaded whitelist with {len(whitelist)} approved users")
        return whitelist
    except Exception as e:
        logger.error(f"Error loading whitelist: {e}")
        return []


def is_whitelisted(username: str) -> bool:
    """
    Check if a username is on the whitelist.
    Returns True if approved, False otherwise.
    """
    whitelist = load_whitelist()
    return username.lower() in [u.lower() for u in whitelist]


def add_to_whitelist(username: str) -> bool:
    """
    Add a username to the whitelist.
    Returns True if successful, False if already exists.
    """
    ensure_data_folder()
    whitelist = load_whitelist()

    # Check if already in whitelist (case-insensitive)
    if any(u.lower() == username.lower() for u in whitelist):
        logger.warning(f"Username '{username}' already in whitelist")
        return False

    whitelist.append(username)

    try:
        with open(WHITELIST_FILE, 'w') as file:
            json.dump({"whitelist": whitelist}, file, indent=2)
        logger.info(f"Added '{username}' to whitelist")
        return True
    except Exception as e:
        logger.error(f"Error updating whitelist: {e}")
        return False


def remove_from_whitelist(username: str) -> bool:
    """
    Remove a username from the whitelist.
    Returns True if successful, False if not found.
    """
    ensure_data_folder()
    whitelist = load_whitelist()

    # Find and remove (case-insensitive)
    original_length = len(whitelist)
    whitelist = [u for u in whitelist if u.lower() != username.lower()]

    if len(whitelist) == original_length:
        logger.warning(f"Username '{username}' not found in whitelist")
        return False

    try:
        with open(WHITELIST_FILE, 'w') as file:
            json.dump({"whitelist": whitelist}, file, indent=2)
        logger.info(f"Removed '{username}' from whitelist")
        return True
    except Exception as e:
        logger.error(f"Error updating whitelist: {e}")
        return False


def get_user_role(username: str) -> str:
    """
    Get the role of a user.
    Returns the role string (admin, user, guest) or None if user not found.
    """
    users = load_users()

    if username not in users:
        return None

    user_data = users[username]
    return user_data.get('role', 'user')  # Default to 'user' if role not specified

