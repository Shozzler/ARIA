# ARIA Development Roadmap

## Overview
This document outlines the step-by-step development plan for ARIA, with security requirements integrated from the start.

---

## Phase 1: Ubiquiti Router Integration (CURRENT PHASE)

**Goal**: Connect to Ubiquiti UniFi API and control network access

**What we'll build:**
1. UniFi API client (talk to router)
2. Get list of connected devices
3. Block/Allow internet access for devices
4. Get network statistics

**Files to create:**
- `src/integrations/unifi.py` - UniFi API connector
- `src/integrations/__init__.py` - Package initializer
- Test the connection locally

**Timeline**: 2-3 days of coding

**Security**: Store UniFi credentials in `.env`, never in code

---

## Phase 2: HomeConnect Integration (After Phase 1)

**Goal**: Connect to HomeConnect API for Fridge and Oven

**What we'll build:**
1. HomeConnect API client
2. Get fridge temperature, door status
3. Get oven status, timer
4. Control basic functions (turn on/off, set temp)

**Files to create:**
- `src/integrations/homeconnect.py` - HomeConnect connector

**Timeline**: 2-3 days

---

## Phase 3: LG WebOS TV Integration (After Phase 2)

**Goal**: Connect to LG TV and control it

**What we'll build:**
1. LG WebOS API client
2. Get TV status (on/off, volume, input)
3. Control TV (power, volume, input)

**Files to create:**
- `src/integrations/lg_webos.py` - LG WebOS connector

**Timeline**: 1-2 days

---

## Phase 4: Web Dashboard Frontend (After Phase 3)

**Goal**: Build web interface to control all devices

**What we'll build:**
1. Login page (username/password)
2. Dashboard showing all devices
3. Control buttons for each device
4. Real-time status updates

**Files to create:**
- `src/api/` - Flask backend API routes
- `src/auth.py` - Login/session management
- `web/` - HTML/CSS/JavaScript frontend

**Timeline**: 3-5 days

---

## Phase 5: Deployment to QNAP (After Phase 4)

**Goal**: Package everything as Docker container for QNAP

**What we'll build:**
1. `Dockerfile` - Container definition
2. `.dockerignore` - What to exclude
3. Test on QNAP
4. Set up automated backups

**Timeline**: 1-2 days

---

## Current Phase: Phase 1 - Ubiquiti Router Integration

### Step-by-Step Plan

**Step 1**: Create UniFi integration file  
**Step 2**: Write code to connect to UniFi API  
**Step 3**: Get list of connected clients  
**Step 4**: Write function to block/allow internet  
**Step 5**: Test everything locally  
**Step 6**: Integrate with DeviceManager  
**Step 7**: Add to main.py to test  

---

## Learning Outcomes by Phase

**Phase 1**: 
- API authentication (username/password)
- HTTP requests with `requests` library
- JSON data parsing
- Error handling

**Phase 2**:
- OAuth2 authentication
- Different API patterns
- Data transformation

**Phase 3**:
- WebSocket connections
- Real-time communication

**Phase 4**:
- Web frameworks (Flask)
- Frontend development (HTML/CSS/JS)
- User authentication
- Session management

**Phase 5**:
- Docker containerization
- Deployment best practices

---

## Next Action

We're starting **Phase 1: Ubiquiti Router Integration**

You will:
1. Create `src/integrations/unifi.py`
2. Write the UniFi API client class
3. Test it connects to your router
4. Learn API integration along the way

Ready? Let's go! 🚀
