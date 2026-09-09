"""
Simple test for the authentication system
"""

from src.auth import User, save_user, login, load_users

print("=" * 50)
print("TESTING ARIA AUTHENTICATION SYSTEM")
print("=" * 50)

# Test 1: Create a user
print("\n1. Creating a new user...")
user1 = User("sean", "password123")
print(f"   Created user: {user1.username}")

# Test 2: Save the user
print("\n2. Saving user to file...")
result = save_user(user1)
print(f"   Save successful: {result}")

# Test 3: Try to save duplicate
print("\n3. Trying to save duplicate (should fail)...")
user1_duplicate = User("sean", "different_password")
result = save_user(user1_duplicate)
print(f"   Save successful: {result} (should be False)")

# Test 4: Load users
print("\n4. Loading users from file...")
users = load_users()
print(f"   Loaded {len(users)} user(s): {list(users.keys())}")

# Test 5: Login with correct password
print("\n5. Testing login with CORRECT password...")
login_result = login("sean", "password123")
print(f"   Login successful: {login_result} (should be True)")

# Test 6: Login with wrong password
print("\n6. Testing login with WRONG password...")
login_result = login("sean", "wrongpassword")
print(f"   Login successful: {login_result} (should be False)")

# Test 7: Login with non-existent user
print("\n7. Testing login with non-existent user...")
login_result = login("john", "password123")
print(f"   Login successful: {login_result} (should be False)")

print("\n" + "=" * 50)
print("TESTING COMPLETE!")
print("=" * 50)