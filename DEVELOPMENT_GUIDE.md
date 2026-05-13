# ARIA Development Guide

This guide explains the project structure and what each component does.

## Project Structure

```
ARIA/
├── main.py                 # Entry point - starts the MCP server
├── requirements.txt        # Python dependencies (pip install -r requirements.txt)
├── README.md              # Project overview
├── .gitignore             # Files to ignore in Git
├── DEVELOPMENT_GUIDE.md   # This file
│
├── config/
│   └── example.env        # Configuration template (copy to .env and fill in)
│
└── src/                   # Source code directory
    ├── __init__.py        # Makes src a Python package
    ├── device_manager.py  # Base classes for device management
    ├── integrations/      # Device-specific API integrations (to be created)
    │   ├── unifi.py       # Ubiquiti UniFi API
    │   ├── homeconnect.py # HomeConnect API
    │   └── lg_webos.py    # LG WebOS API
    └── mcp_server.py      # MCP server logic (to be created)
```

---

## File Explanations

### `main.py` - The Starting Point

This is the **entry point** of your entire application. When you run `python main.py`, this file starts first.

**What it does:**
1. Sets up logging (so you can see what's happening)
2. Initializes the ARIA system
3. Starts the MCP server
4. Keeps the program running

**Key Concepts:**
- **Logging**: A way to print messages with color and timestamps (better than print())
- **try/except**: Catches errors gracefully
- **KeyboardInterrupt**: Allows you to stop the server with Ctrl+C

---

### `src/device_manager.py` - Managing Devices

This file contains the **base classes** that all devices will use.

**Key Classes:**

#### 1. `Device` (Abstract Base Class)
- This is a **template** that all smart home devices must follow
- Think of it as a "contract" - every device must have these methods:
  - `connect()` - Connect to the device
  - `disconnect()` - Disconnect from the device
  - `get_status()` - Get the device's current state

**Why Abstract?** 
- A fridge connects differently than a TV
- But they should all be able to do the same things (connect, disconnect, get status)
- Abstract class enforces this

**Example:**
```python
class FridgeDevice(Device):
    def connect(self):
        # Connect to HomeConnect API
        pass
    
    def get_status(self):
        # Get fridge temperature, door status, etc.
        pass
```

#### 2. `DeviceManager`
- This is like a **receptionist** for all your devices
- It keeps track of all connected devices
- It routes commands to the right device

**Methods:**
- `register_device()` - Add a new device
- `get_device()` - Find a device by ID
- `get_all_status()` - Get status of all devices

**Example:**
```python
manager = DeviceManager()
fridge = FridgeDevice("fridge_01", "Kitchen Fridge", "fridge")
manager.register_device(fridge)
status = manager.get_all_status()
# Returns: {"fridge_01": {"temperature": 4, "door": "closed"}}
```

---

### `requirements.txt` - Dependencies

This file lists all Python packages your project needs.

**Current packages:**
- `requests` - For making HTTP calls to APIs
- `flask` - For the web server/dashboard
- `python-dotenv` - For reading .env configuration
- `colorlog` - For colored logging output

**How to use it:**
```bash
pip install -r requirements.txt
```

---

### `config/example.env` - Configuration Template

This is where you store **secrets** and **settings** that shouldn't be in code.

**Why separate from code?**
- Your API keys are sensitive
- You don't want to accidentally commit them to Git
- Different environments (home, cloud, test) need different settings

**How to use:**
1. Copy `config/example.env` to `config/.env`
2. Fill in your actual credentials
3. Python code reads from `.env` using `python-dotenv`

**Never commit `.env` to Git!** (That's why it's in `.gitignore`)

---

## Development Workflow

### Step 1: Set Up Environment
```bash
# Navigate to project folder
cd C:\Users\sford\Documents\ARIA

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Settings
```bash
# Copy example config
copy config\example.env config\.env

# Edit config/.env and fill in your actual values
```

### Step 3: Run the Server
```bash
python main.py
```

You should see colored log messages showing ARIA is running.

---

## Key Programming Concepts Used

### 1. **Abstract Base Classes (ABC)**
- Defines a "contract" that subclasses must follow
- Ensures consistency across different device types
- Forces implementation of required methods

### 2. **Dictionary Data Structure**
```python
devices = {
    "tv_01": TVDevice(...),
    "fridge_01": FridgeDevice(...),
    "router_01": RouterDevice(...)
}
```
- Fast lookup by device_id
- Easy to iterate over all devices

### 3. **Type Hints**
```python
def get_device(self, device_id: str) -> Device:
```
- `str` = input must be a string
- `-> Device` = function returns a Device object
- Makes code clearer and catches errors

### 4. **Logging Instead of Print**
```python
logger.info("Device connected")  # Good
print("Device connected")        # Bad practice
```
- Structured output with timestamps
- Can be directed to files
- Different log levels (DEBUG, INFO, WARNING, ERROR)

---

## Next Steps

We'll build device-specific integrations:

1. **UniFi Integration** - Connect to Ubiquiti router/doorbell
2. **HomeConnect Integration** - Connect to fridge/oven
3. **LG WebOS Integration** - Connect to TV
4. **Web Dashboard** - Build the frontend interface
5. **MCP Server** - Set up the request/response handling
6. **Docker** - Containerize for QNAP deployment

---

## Learning Goals

By building ARIA, you'll learn:
- ✅ Python OOP (Object-Oriented Programming)
- ✅ API integration (REST APIs)
- ✅ Async programming (for handling multiple devices)
- ✅ Web development (Flask, HTML, JavaScript)
- ✅ Docker containerization
- ✅ Project structure and best practices
- ✅ Configuration management
- ✅ Error handling and logging

---

## Questions to Ask Yourself

As you build, think about:
1. Why use abstract classes instead of just one Device class?
2. Why keep secrets in `.env` instead of in Python files?
3. Why use a DeviceManager instead of a simple list?
4. How would you add a new device type?
5. What happens if a device goes offline?

These questions will deepen your understanding! 🚀

