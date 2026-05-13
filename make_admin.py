"""
Helper script to make a user an admin.
Run this once to set up your admin account.

Usage:
    python make_admin.py
"""

from src.auth import load_users, USERS_FILE
import json
import os

def make_admin(username):
    """Make a user an admin"""
    users = load_users()

    if username not in users:
        print(f"❌ User '{username}' not found")
        return False

    # Update the role
    users[username]['role'] = 'admin'

    # Save back to file
    try:
        with open(USERS_FILE, 'w') as file:
            json.dump(users, file, indent=2)
        print(f"✅ User '{username}' is now an admin!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("ARIA - Make User Admin")
    print("-" * 40)

    username = input("Enter username to make admin: ").strip()

    if not username:
        print("❌ Username cannot be empty")
    else:
        make_admin(username)
