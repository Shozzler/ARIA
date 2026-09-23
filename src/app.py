"""
Flask Web Application for ARIA
Handles web interface and routing
"""

import os
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash
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
from src.integrations.miele import MieleClient
from src.integrations.webos_tv import WebOSTVClient
from src.activity import (
    record_visit, record_action, get_activity, toggle_pin, relative_time, DASHBOARD_LIMIT
)
from flask_wtf import CSRFProtect

# Load .env before anything below reads from it (app.secret_key included)
load_dotenv()

# Get the directory where app.py is located
# Then go up one level to ARIA root, then find templates/ and static/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Initialize Flask app with absolute paths
app = Flask(__name__,
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is not set in .env - generate one with: "
        "python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# Protects every POST/PUT/PATCH/DELETE route against CSRF by default.
# Forms need a csrf_token field; JS fetch() calls need an X-CSRFToken header.
csrf = CSRFProtect(app)

# HomeConnect allows only 50 API calls per minute. The appliance list and each
# appliance's program list barely ever change, so we cache them for a while
# instead of re-fetching on every page load - this is what keeps the auto-refresh
# on /homeconnect from tripping the rate limit.
_program_options_cache = {}
_appliances_cache = {"data": None, "fetched_at": 0}
_available_programs_cache = {}  # haId -> {"data": [...], "fetched_at": ...}
CACHE_TTL_SECONDS = 300  # 5 minutes


def get_cached_appliances(client):
    # Get the appliance list, from cache when it is fresh enough.
    # Falls back to the last known list if a live fetch fails (e.g. a
    # temporary rate limit) instead of showing an error for no reason.
    now = time.time()
    if _appliances_cache["data"] is not None and now - _appliances_cache["fetched_at"] < CACHE_TTL_SECONDS:
        return _appliances_cache["data"]

    appliances = client.get_appliances()
    if appliances is not None:
        _appliances_cache["data"] = appliances
        _appliances_cache["fetched_at"] = now
        return appliances

    return _appliances_cache["data"]  # None if we have never had a successful fetch


def get_cached_programs(client, ha_id):
    # Get one appliance's available-programs list, from cache when fresh enough.
    now = time.time()
    cached = _available_programs_cache.get(ha_id)
    if cached is not None and now - cached["fetched_at"] < CACHE_TTL_SECONDS:
        return cached["data"]

    programs = client.get_available_programs(ha_id)
    if programs is not None:
        _available_programs_cache[ha_id] = {"data": programs, "fetched_at": now}
        return programs

    return cached["data"] if cached is not None else None


_status_cache = {}  # haId -> {"data": ..., "fetched_at": ...}
STATUS_CACHE_TTL_SECONDS = 45  # short - status changes while a program runs


def get_cached_status(client, ha_id):
    # Get one appliance's live status, from a short cache. Status changes
    # while a program is running (temperature climbing) so this TTL is much
    # shorter than the other caches - just enough to survive a quick
    # double page-load without doubling the API calls.
    now = time.time()
    cached = _status_cache.get(ha_id)
    if cached is not None and now - cached["fetched_at"] < STATUS_CACHE_TTL_SECONDS:
        return cached["data"]

    status = client.get_appliance_status(ha_id)
    if status is not None:
        _status_cache[ha_id] = {"data": status, "fetched_at": now}
        return status

    return cached["data"] if cached is not None else None

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

    username = session['username']
    recent = get_activity(username, limit=DASHBOARD_LIMIT)

    # Enrich appliance actions with a live status line, reusing the same
    # short-lived cache HomeConnect calls elsewhere use to stay rate-limit safe.
    ha_ids_needed = {
        e['meta']['ha_id'] for e in recent
        if e['kind'] == 'action' and e.get('meta', {}).get('ha_id')
    }
    if ha_ids_needed:
        load_dotenv()
        base_url = os.getenv("HOMECONNECT_BASE_URL", "https://simulator.home-connect.com")
        client = HomeConnectClient(base_url=base_url)
        for appliance in (get_cached_appliances(client) or []):
            if appliance['haId'] not in ha_ids_needed:
                continue
            status = get_cached_status(client, appliance['haId'])
            live = {
                'status_display': format_status(status) if status else [],
                'connected': appliance.get('connected', False),
            }
            for e in recent:
                if e['kind'] == 'action' and e.get('meta', {}).get('ha_id') == appliance['haId']:
                    e['live'] = live

    for e in recent:
        e['last_used_display'] = relative_time(e.get('last_used', ''))

    return render_template('dashboard.html', username=username, recent=recent)

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

        record_visit(session['username'], 'network', 'Network', url_for('dreammachine'))

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
    
# Display-name overrides: Sean's own naming, applied on top of whatever
# the real HomeConnect/Miele accounts call these appliances.
DISPLAY_NAME_OVERRIDES = {
    "Four": "Four à vapeur",
    "Four 2": "Four",
}

# Route: Appliances Dashboard (icon grid - HomeConnect + Miele together)
@app.route('/homeconnect')
def homeconnect():
    """Show all appliances (HomeConnect + Miele) as a clickable icon grid"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    load_dotenv()
    base_url = os.getenv("HOMECONNECT_BASE_URL", "https://simulator.home-connect.com")
    client = HomeConnectClient(base_url=base_url)
    appliances = get_cached_appliances(client)

    cards = []

    if appliances is None:
        flash("Could not fetch HomeConnect appliances. Have you logged in with homeconnect_login.py?", "error")
    else:
        for appliance in appliances:
            display_name = DISPLAY_NAME_OVERRIDES.get(appliance.get('name'), appliance.get('name'))
            cards.append({
                'display_name': display_name,
                'type': appliance.get('type'),
                'detail_url': url_for('homeconnect_detail', ha_id=appliance['haId']),
            })

    miele_client = MieleClient()
    miele_appliances = miele_client.get_appliances()

    if miele_appliances is None:
        flash("Could not fetch Miele appliances. Have you logged in with miele_login.py?", "error")
    else:
        for appliance in miele_appliances:
            ident = appliance.get('ident', {})
            type_label = ident.get('type', {}).get('value_localized', 'Appliance')
            display_name = ident.get('deviceName') or type_label
            cards.append({
                'display_name': display_name,
                'type': type_label,
                'detail_url': url_for('miele_detail', device_id=appliance['id']),
            })

    record_visit(session['username'], 'appliances', 'Appliances', url_for('homeconnect'))

    return render_template('homeconnect.html',
        username=session['username'],
        cards=cards,
        appliance_count=len(cards))

# Route: HomeConnect appliance detail page
@app.route('/homeconnect/<ha_id>')
def homeconnect_detail(ha_id):
    """Show one HomeConnect appliance's details, status, and controls"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    load_dotenv()
    base_url = os.getenv("HOMECONNECT_BASE_URL", "https://simulator.home-connect.com")
    client = HomeConnectClient(base_url=base_url)

    appliances = get_cached_appliances(client) or []
    appliance_info = next((a for a in appliances if a.get('haId') == ha_id), None)
    if not appliance_info:
        flash("Appliance not found.", "error")
        return redirect(url_for('homeconnect'))

    display_name = DISPLAY_NAME_OVERRIDES.get(appliance_info.get('name'), appliance_info.get('name'))

    status = get_cached_status(client, ha_id)
    status_display = format_status(status) if status else []

    settings = client.get_appliance_settings(ha_id)
    power_state = None
    if settings:
        for item in settings:
            if item.get('key') == 'BSH.Common.Setting.PowerState':
                power_state = item.get('value', '').split('.')[-1]

    programs = get_cached_programs(client, ha_id) or []
    for program in programs:
        cache_key = (ha_id, program['key'])
        if cache_key in _program_options_cache:
            program['temperature'] = _program_options_cache[cache_key]
        else:
            program_options = client.get_program_options(ha_id, program['key'])
            program['temperature'] = None
            if program_options:
                for opt in program_options:
                    if opt.get('key') == 'Cooking.Oven.Option.SetpointTemperature':
                        program['temperature'] = opt.get('constraints', {})
                        break
            _program_options_cache[cache_key] = program['temperature']

    return render_template('homeconnect_detail.html',
        username=session['username'],
        ha_id=ha_id,
        display_name=display_name,
        type=appliance_info.get('type'),
        brand=appliance_info.get('brand'),
        connected=appliance_info.get('connected'),
        status_display=status_display,
        power_state=power_state,
        programs=programs)

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

    success = client.set_appliance_setting(ha_id, "BSH.Common.Setting.PowerState", new_value)
    if success:
        flash("Power updated.", "success")
        new_state_label = "On" if new_value.endswith("On") else "Off"
        appliance_name = ha_id
        for appliance in (get_cached_appliances(client) or []):
            if appliance.get('haId') == ha_id:
                appliance_name = appliance.get('name', ha_id)
                break
        record_action(session['username'], ha_id, 'power',
                       f"Turned {new_state_label} {appliance_name}",
                       url_for('homeconnect_detail', ha_id=ha_id))
    else:
        flash("Could not change power state - the appliance may need remote control enabled on its own panel.", "error")

    return redirect(url_for('homeconnect_detail', ha_id=ha_id))

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
    temperature = request.form.get('temperature')
    if program_key:
        options = None
        if temperature:
            options = [{
                "key": "Cooking.Oven.Option.SetpointTemperature",
                "value": int(temperature),
                "unit": "°C"
            }]
        success, error_message = client.start_program(ha_id, program_key, options)
        program_name = program_key.split('.')[-1]
        if success:
            temp_note = f" at {temperature}°C" if temperature else ""
            flash(f"Started {program_name}{temp_note}.", "success")
            appliance_name = ha_id
            for appliance in (get_cached_appliances(client) or []):
                if appliance.get('haId') == ha_id:
                    appliance_name = appliance.get('name', ha_id)
                    break
            record_action(session['username'], ha_id, 'program',
                           f"Started {program_name}{temp_note} on {appliance_name}",
                           url_for('homeconnect_detail', ha_id=ha_id),
                           program_key=program_key,
                           temperature=temperature)
        else:
            flash(f"Could not start {program_name}: {error_message}", "error")

    return redirect(url_for('homeconnect_detail', ha_id=ha_id))

# Route: Stop the currently running program on an appliance
@app.route('/homeconnect/<ha_id>/stop-program', methods=['POST'])
def stop_appliance_program(ha_id):
    """Stop whatever program is currently running on an appliance"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    load_dotenv()
    base_url = os.getenv("HOMECONNECT_BASE_URL", "https://simulator.home-connect.com")
    client = HomeConnectClient(base_url=base_url)

    success, error_message = client.stop_program(ha_id)
    if success:
        flash("Program stopped.", "success")
        appliance_name = ha_id
        for appliance in (get_cached_appliances(client) or []):
            if appliance.get('haId') == ha_id:
                appliance_name = appliance.get('name', ha_id)
                break
        record_action(session['username'], ha_id, 'program',
                       f"Stopped program on {appliance_name}",
                       url_for('homeconnect_detail', ha_id=ha_id))
    else:
        flash(f"Could not stop the program: {error_message}", "error")

    return redirect(url_for('homeconnect_detail', ha_id=ha_id))

# Route: Miele appliance detail page
@app.route('/miele/<device_id>')
def miele_detail(device_id):
    """Show one Miele appliance's details, status, and controls"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    client = MieleClient()
    appliances = client.get_appliances() or []
    appliance_info = next((a for a in appliances if a.get('id') == device_id), None)
    if not appliance_info:
        flash("Appliance not found.", "error")
        return redirect(url_for('homeconnect'))

    ident = appliance_info.get('ident', {})
    state = appliance_info.get('state', {})
    type_label = ident.get('type', {}).get('value_localized', 'Appliance')
    display_name = ident.get('deviceName') or type_label

    actions = client.get_appliance_actions(device_id) or {}
    can_power_on = bool(actions.get('powerOn'))

    detail_fields = []
    for key in ('status', 'programType', 'programPhase'):
        field = state.get(key)
        if isinstance(field, dict) and field.get('value_localized'):
            detail_fields.append({
                'label': field.get('key_localized', key),
                'value': field.get('value_localized'),
            })

    return render_template('miele_detail.html',
        username=session['username'],
        device_id=device_id,
        display_name=display_name,
        type=type_label,
        model=ident.get('deviceIdentLabel', {}).get('techType'),
        detail_fields=detail_fields,
        can_power_on=can_power_on)

# Route: Turn a Miele appliance on
@app.route('/miele/<device_id>/power-on', methods=['POST'])
def miele_power_on(device_id):
    """Turn on a Miele appliance"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    client = MieleClient()
    success = client.set_appliance_power(device_id, on=True)

    if success:
        flash("Power on sent.", "success")
        record_action(session['username'], device_id, 'power',
                       f"Turned on {device_id}", url_for('miele_detail', device_id=device_id))
    else:
        flash("Could not turn on the appliance.", "error")

    return redirect(url_for('miele_detail', device_id=device_id))

# Route: LG TV status and controls
@app.route('/tv')
def tv():
    """Show the LG TV's status and controls"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    tv_ip = os.getenv("TV_IP")
    status = None
    paired = False

    if not tv_ip:
        flash("TV_IP is not set in .env.", "error")
    else:
        client = WebOSTVClient(tv_ip)
        paired = os.path.exists(client.key_file)
        if not paired:
            flash("The TV hasn't been paired yet - run pair_tv.py once, locally.", "error")
        else:
            status = client.get_status()
            if status is None:
                flash("Could not reach the TV. Is it turned on?", "error")

    record_visit(session['username'], 'tv', 'TV', url_for('tv'))

    return render_template('tv.html',
        username=session['username'],
        tv_ip=tv_ip,
        paired=paired,
        status=status)

# Route: Turn the TV on (Wake-on-LAN)
@app.route('/tv/power-on', methods=['POST'])
def tv_power_on():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    tv_ip = os.getenv("TV_IP")
    tv_mac = os.getenv("TV_MAC")
    if not tv_mac:
        flash("TV_MAC is not set in .env.", "error")
        return redirect(url_for('tv'))

    client = WebOSTVClient(tv_ip, mac=tv_mac)
    if client.power_on():
        # Wake-on-LAN gets no reply, so wait for the TV to boot before
        # reloading the page - otherwise it would still show as off.
        time.sleep(8)
        flash("Turn-on signal sent to the TV.", "success")
        record_action(session['username'], 'lg_tv', 'power', "Turned on LG TV", url_for('tv'))
    else:
        flash("Could not send the turn-on signal to the TV.", "error")

    return redirect(url_for('tv'))

# Route: Turn the TV off
@app.route('/tv/power-off', methods=['POST'])
def tv_power_off():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    tv_ip = os.getenv("TV_IP")
    if not tv_ip:
        flash("TV_IP is not set in .env.", "error")
        return redirect(url_for('tv'))

    client = WebOSTVClient(tv_ip)
    if client.power_off():
        flash("TV turned off.", "success")
        record_action(session['username'], 'lg_tv', 'power', "Turned off LG TV", url_for('tv'))
    else:
        flash("Could not turn off the TV.", "error")

    return redirect(url_for('tv'))

# Route: Mute/unmute the TV
@app.route('/tv/mute', methods=['POST'])
def tv_mute():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    tv_ip = os.getenv("TV_IP")
    if not tv_ip:
        flash("TV_IP is not set in .env.", "error")
        return redirect(url_for('tv'))

    client = WebOSTVClient(tv_ip)
    status = client.get_status()
    currently_muted = bool(status.get('muted')) if status else False

    if client.set_mute(not currently_muted):
        flash("TV unmuted." if currently_muted else "TV muted.", "success")
    else:
        flash("Could not change the TV's mute state.", "error")

    return redirect(url_for('tv'))

# Route: Step the TV's volume up or down
@app.route('/tv/volume/<direction>', methods=['POST'])
def tv_volume(direction):
    if 'username' not in session:
        return redirect(url_for('login_page'))

    if direction not in ('up', 'down'):
        flash("Invalid volume direction.", "error")
        return redirect(url_for('tv'))

    tv_ip = os.getenv("TV_IP")
    if not tv_ip:
        flash("TV_IP is not set in .env.", "error")
        return redirect(url_for('tv'))

    client = WebOSTVClient(tv_ip)
    ok = client.volume_up() if direction == 'up' else client.volume_down()
    if not ok:
        flash("Could not change the TV's volume.", "error")

    return redirect(url_for('tv'))

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

    record_visit(session['username'], 'admin', 'Admin', url_for('admin_users'))

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

    record_visit(session['username'], 'all-devices', 'All Devices', url_for('all_devices'))

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

# Route: Full activity history
@app.route('/history')
def history():
    """Show the full recent-activity history (not just the dashboard's capped view)"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    entries = get_activity(session['username'])
    for e in entries:
        e['last_used_display'] = relative_time(e.get('last_used', ''))

    return render_template('history.html', username=session['username'], entries=entries)

# Route: Pin/unpin a recent-activity entry
@app.route('/api/activity/pin', methods=['POST'])
def api_toggle_pin():
    """Toggle the pinned state of one activity entry, then go back where we came from"""
    if 'username' not in session:
        return redirect(url_for('login_page'))

    entry_id = request.form.get('entry_id')
    if entry_id:
        toggle_pin(session['username'], entry_id)

    return redirect(request.referrer or url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)