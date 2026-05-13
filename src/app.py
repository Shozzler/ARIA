"""
Flask Web Application for ARIA
Handles web interface and routing
"""

import os
from flask import Flask, render_template, request, redirect, url_for, session
import logging
from src.auth import login, save_user, User

# Get the directory where app.py is located
# Then go up one level to ARIA root, then find templates/ and static/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Initialize Flask app with absolute paths
app = Flask(__name__,
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)
app.secret_key = "your-secret-key-change-this"  # For sessions

logger = logging.getLogger(__name__)

# Route: Home page (redirect to login)
@app.route('/')
def home():
    """Redirect to login page"""
    return redirect(url_for('login_page'))

# Route: Login page (GET - show form)
@app.route('/login', methods=['GET'])
def login_page():
    """Show login page"""
    return render_template('login.html')

# Route: Login submission (POST - process login)
@app.route('/login', methods=['POST'])
def login_submit():
    """Process login form submission"""
    username = request.form.get('username')
    password = request.form.get('password')

    # Try to login
    if login(username, password):
        session['username'] = username
        logger.info(f"User {username} logged in successfully")
        return redirect(url_for('dashboard'))
    else:
        logger.warning(f"Failed login attempt for {username}")
        return render_template('login.html', error="Invalid username or password")

# Route: Sign up page (GET - show form)
@app.route('/signup', methods=['GET'])
def signup_page():
    """Show signup page"""
    return render_template('signup.html')

# Route: Sign up submission (POST - process signup)
@app.route('/signup', methods=['POST'])
def signup_submit():
    """Process signup form submission"""
    username = request.form.get('username')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')

    # Validate input
    if not username or len(username) < 3:
        return render_template('signup.html', error="Username must be at least 3 characters")

    if not password or len(password) < 8:
        return render_template('signup.html', error="Password must be at least 8 characters")

    if password != password_confirm:
        return render_template('signup.html', error="Passwords do not match")

    # Try to create user
    try:
        user = User(username, password)
        if save_user(user):
            logger.info(f"New user {username} registered successfully")
            return render_template('signup.html', success="Account created! You can now login.")
        else:
            return render_template('signup.html', error="Username already exists")
    except Exception as e:
        logger.error(f"Error creating user {username}: {str(e)}")
        return render_template('signup.html', error="Error creating account. Please try again.")

# Route: Dashboard (GET - show after login)
@app.route('/dashboard')
def dashboard():
    """Show dashboard (only for logged in users)"""
    if 'username' not in session:
        return redirect(url_for('login_page'))
    
    return render_template('dashboard.html', username=session['username'])

# Route: Logout
@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username')
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)