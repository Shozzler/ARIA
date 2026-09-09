"""
Flask Web Application for ARIA
Handles web interface and routing
"""

import os
from flask import Flask, render_template, request, redirect, url_for, session
import logging
from src.auth import (
    login, save_user, User, is_whitelisted,
    get_user_role, load_whitelist, add_to_whitelist,
    remove_from_whitelist, load_users, USERS_FILE
)
from src.integrations.unifi import UniFiClient
from src.integrations.unifi import UniFiClient
from src.device_categorizer import categorize_device
from dotenv import load_dotenv
import json

from src.integrations.unifi import UniFiClient
from src.integrations.homeconnect import HomeConnectClient, format_status

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
        session['role'] = get_user_role(username)  # Store role in session
        logger.info(f"User {username} logged in successfully (role: {session['role']})")
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

    # Check if username is whitelisted
    if not is_whitelisted(username):
        logger.warning(f"Signup attempt for non-whitelisted user: {username}")
        return render_template('signup.html', error="This username is not authorized. Contact the admin.")

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

# Route: Dream Machine / Network Dashboard
@app.route('/dreammachine')
def dreammachine():
    """Show Dream Machine network dashboard"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    # Load environment variables
    load_dotenv()
    controller_ip = os.getenv("UNIFI_CONTROLLER_IP", "10.20.40.1")
    site_id = os.getenv("UNIFI_SITE_ID")
    api_key = os.getenv("UNIFI_API_KEY")

    # Check if credentials are available
    if not site_id or not api_key:
        return render_template('dreammachine.html',
                             username=session['username'],
                             error="UniFi credentials not configured in .env file")

    try:
        # Initialize UniFi client
        client = UniFiClient(
            controller_ip=controller_ip,
            api_key=api_key,
            verify_ssl=False
        )

        # Get all data
        devices = client.get_devices(site_id)
        cameras = client.list_cameras(site_id)
        clients = client.get_all_clients(site_id)

        # Prepare data for template
        device_list = []
        camera_list = []
        client_list = []

        if devices:
            for device in devices:
                device_list.append({
                    'name': device.get('name', 'Unknown'),
                    'model': device.get('model', 'Unknown'),
                    'ip': device.get('ipAddress', 'N/A'),
                    'mac': device.get('macAddress', 'N/A'),
                    'status': device.get('state', 'unknown'),
                    'firmware': device.get('firmwareVersion', 'N/A')
                })

        if cameras:
            for camera in cameras:
                camera_list.append({
                    'name': camera.get('name', 'Unknown'),
                    'model': camera.get('model', 'Unknown'),
                    'ip': camera.get('ipAddress', 'N/A'),
                    'mac': camera.get('macAddress', 'N/A'),
                    'status': camera.get('state', 'unknown')
                })

        if clients:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)

            for client_item in clients:
                # Parse connection timestamp and calculate time since connected
                connected_at = client_item.get('connectedAt', 'N/A')
                connected_time = 'N/A'

                try:
                    if connected_at and connected_at != 'N/A':
                        # Handle ISO format string (e.g., "2026-03-24T02:58:15Z")
                        if isinstance(connected_at, str):
                            connected_dt = datetime.fromisoformat(connected_at.replace('Z', '+00:00'))
                        # Handle Unix timestamp (milliseconds)
                        elif isinstance(connected_at, (int, float)):
                            connected_dt = datetime.fromtimestamp(connected_at / 1000, tz=timezone.utc)
                        else:
                            connected_dt = None

                        if connected_dt:
                            # Calculate time difference
                            time_diff = now - connected_dt
                            seconds = time_diff.total_seconds()

                            # Format as relative time
                            if seconds < 60:
                                connected_time = f"{int(seconds)} seconds ago"
                            elif seconds < 3600:
                                minutes = int(seconds / 60)
                                connected_time = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                            elif seconds < 86400:
                                hours = int(seconds / 3600)
                                connected_time = f"{hours} hour{'s' if hours != 1 else ''} ago"
                            elif seconds < 604800:
                                days = int(seconds / 86400)
                                connected_time = f"{days} day{'s' if days != 1 else ''} ago"
                            else:
                                weeks = int(seconds / 604800)
                                connected_time = f"{weeks} week{'s' if weeks != 1 else ''} ago"
                except Exception as e:
                    logger.warning(f"Could not parse connection time: {e}")
                    connected_time = 'N/A'

                client_list.append({
                    'name': client_item.get('name', 'Unknown'),
                    'ip': client_item.get('ipAddress', 'N/A'),
                    'mac': client_item.get('macAddress', 'N/A'),
                    'type': client_item.get('type', 'UNKNOWN'),
                    'connected_at': connected_time,
                    'category': categorize_device(client_item.get('name', 'Unknown'))
                })

        return render_template('dreammachine.html',
                             username=session['username'],
                             devices=device_list,
                             cameras=camera_list,
                             clients=client_list,
                             device_count=len(device_list),
                             camera_count=len(camera_list),
                             client_count=len(client_list))

    except Exception as e:
        logger.error(f"Error fetching Dream Machine data: {str(e)}")
        return render_template('dreammachine.html',
                             username=session['username'],
                             error=f"Error connecting to Dream Machine: {str(e)}")
    
# Route: HomeConnect / Appliances Dashboard
@app.route('/homeconnect')
def homeconnect():
    """Show HomeConnect appliances dashboard"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    load_dotenv()
    base_url = os.getenv("HOMECONNECT_BASE_URL", "https://simulator.home-connect.com")

    client = HomeConnectClient(base_url=base_url)
    appliances = client.get_appliances()

    if appliances is None:
        return render_template('homeconnect.html',
                             username=session['username'],
                             error="Could not fetch appliances. Have you logged in with homeconnect_login.py?")

    for appliance in appliances:
        status = client.get_appliance_status(appliance['haId'])
        appliance['status_display'] = format_status(status) if status else []

        settings = client.get_appliance_settings(appliance['haId'])
        appliance['power_state'] = None
        programs = client.get_available_programs(appliance['haId'])
        appliance['programs'] = programs if programs else []
        if settings:
            for item in settings:
                if item.get('key') == 'BSH.Common.Setting.PowerState':
                    appliance['power_state'] = item.get('value', '').split('.')[-1]
    return render_template('homeconnect.html',
        username=session['username'],
        appliances=appliances,
        appliance_count=len(appliances))

# Route: Toggle appliance power state
@app.route('/homeconnect/<ha_id>/toggle-power', methods=['POST'])
def toggle_appliance_power(ha_id):
    """Flip an appliance's PowerState between On and Standby"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    load_dotenv()
    base_url = os.getenv("HOMECONNECT_BASE_URL", "https://simulator.home-connect.com")
    client = HomeConnectClient(base_url=base_url)

    current_state = request.form.get('current_state')
    new_value = "BSH.Common.EnumType.PowerState.Standby" if current_state == "On" else "BSH.Common.EnumType.PowerState.On"

    client.set_appliance_setting(ha_id, "BSH.Common.Setting.PowerState", new_value)

    return redirect(url_for('homeconnect'))

# Route: Start a program on an appliance
@app.route('/homeconnect/<ha_id>/start-program', methods=['POST'])
def start_appliance_program(ha_id):
    """Start the selected program on an appliance"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    load_dotenv()
    base_url = os.getenv("HOMECONNECT_BASE_URL", "https://simulator.home-connect.com")
    client = HomeConnectClient(base_url=base_url)

    program_key = request.form.get('program_key')
    if program_key:
        client.start_program(ha_id, program_key)

    return redirect(url_for('homeconnect'))
# Route: Logout
@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username')
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for('login_page'))

# Route: User management (admin only)
@app.route('/admin/users')
def admin_users():
    """Show user management page (admin only)"""
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))

    whitelist = load_whitelist()
    all_users = load_users()

    return render_template('admin_users.html',
                         username=session['username'],
                         current_username=session['username'],
                         whitelist=whitelist,
                         all_users=all_users)

# Route: All Devices (flat list of every individual device)
@app.route('/all-devices')
def all_devices():
    """Show every individual device, regardless of category"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    return render_template('all_devices.html', username=session['username'])

# Route: Add user to whitelist (admin only)
@app.route('/api/whitelist/add', methods=['POST'])
def api_add_whitelist():
    """API to add user to whitelist"""
    if 'username' not in session or session.get('role') != 'admin':
        return {'success': False, 'error': 'Unauthorized'}, 403

    new_username = request.form.get('username', '').strip()

    if not new_username or len(new_username) < 3:
        return {'success': False, 'error': 'Username must be at least 3 characters'}, 400

    if add_to_whitelist(new_username):
        logger.info(f"Admin {session['username']} added {new_username} to whitelist")
        return {'success': True, 'message': f'{new_username} added to whitelist'}
    else:
        return {'success': False, 'error': 'Username already in whitelist'}, 400

# Route: Remove user from whitelist (admin only)
@app.route('/api/whitelist/remove', methods=['POST'])
def api_remove_whitelist():
    """API to remove user from whitelist"""
    if 'username' not in session or session.get('role') != 'admin':
        return {'success': False, 'error': 'Unauthorized'}, 403

    remove_username = request.form.get('username', '').strip()

    # Don't allow removing yourself
    if remove_username.lower() == session['username'].lower():
        return {'success': False, 'error': 'Cannot remove yourself from whitelist'}, 400

    if remove_from_whitelist(remove_username):
        logger.info(f"Admin {session['username']} removed {remove_username} from whitelist")
        return {'success': True, 'message': f'{remove_username} removed from whitelist'}
    else:
        return {'success': False, 'error': 'User not in whitelist'}, 400

# Route: Promote user to admin (admin only)
@app.route('/api/users/promote', methods=['POST'])
def api_promote_user():
    """API to promote user to admin"""
    if 'username' not in session or session.get('role') != 'admin':
        return {'success': False, 'error': 'Unauthorized'}, 403

    username = request.form.get('username', '').strip()
    users = load_users()

    if username not in users:
        return {'success': False, 'error': 'User not found'}, 404

    users[username]['role'] = 'admin'

    try:
        with open(USERS_FILE, 'w') as file:
            json.dump(users, file, indent=2)
        logger.info(f"Admin {session['username']} promoted {username} to admin")
        return {'success': True, 'message': f'{username} is now an admin'}
    except Exception as e:
        logger.error(f"Error promoting user: {str(e)}")
        return {'success': False, 'error': 'Error promoting user'}, 500

# Route: Demote user from admin (admin only)
@app.route('/api/users/demote', methods=['POST'])
def api_demote_user():
    """API to demote user from admin"""
    if 'username' not in session or session.get('role') != 'admin':
        return {'success': False, 'error': 'Unauthorized'}, 403

    username = request.form.get('username', '').strip()

    # Don't allow demoting yourself
    if username.lower() == session['username'].lower():
        return {'success': False, 'error': 'Cannot demote yourself'}, 400

    users = load_users()

    if username not in users:
        return {'success': False, 'error': 'User not found'}, 404

    users[username]['role'] = 'user'

    try:
        with open(USERS_FILE, 'w') as file:
            json.dump(users, file, indent=2)
        logger.info(f"Admin {session['username']} demoted {username} from admin")
        return {'success': True, 'message': f'{username} is no longer an admin'}
    except Exception as e:
        logger.error(f"Error demoting user: {str(e)}")
        return {'success': False, 'error': 'Error demoting user'}, 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)