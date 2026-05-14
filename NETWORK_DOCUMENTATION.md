# ARIA Network Documentation

## Network Overview

**Home Network Name:** Ford Household  
**Controller:** UniFi Dream Machine  
**Controller IP:** 10.20.40.1  
**Main Network:** 10.20.40.0/26  
**Guest Network:** 10.20.80.0/27  

---

## Network Devices

### Cameras (4 Total - All G4 Pro except Doorbell)

| Device Name | Model | IP Address | Location | Status | Notes |
|---|---|---|---|---|---|
| Garden-kitchen | G4 Pro | 10.20.40.7 | Garden/Kitchen area | Connected | Read-only access |
| Main Entrance | G4 Pro | 10.20.40.22 | Main entrance | Connected | Read-only access |
| Main Door Bell | G4 Doorbell Pro | 10.20.40.56 | Main door | Connected | Read-only access |
| Daisy Entrance | G4 Pro | 10.20.40.15 | Entrance (Daisy) | Connected | Read-only access |

**Camera API:** UniFi Video API (via Dream Machine)

---

### Smart Home Devices (4 Total)

| Device Name | Model | IP Address | API Type | Status | Notes |
|---|---|---|---|---|---|
| Gaggenau Oven 1 | Geggenau | 10.20.40.24 | HomeConnect | Connected | Read-only access |
| Gaggenau Oven 2 | Geggenau | 10.20.40.5 | HomeConnect | Connected | Read-only access |
| Siemens Fridge | Siemens | 10.20.40.57 | HomeConnect | Connected | Read-only access |
| LG TV | LG WebOS | 10.20.40.59 | WebOS API | Connected | Read-only access |

---

## UniFi Dream Machine API

### API Endpoint
```
https://10.20.40.1/proxy/network/integration/v1/
```

### Authentication
- **Method:** API Key
- **Header:** `X-API-KEY: YOUR_API_KEY`
- **Header:** `Accept: application/json`

### Available Endpoints (Read-Only for Now)

#### Get All Sites
```
GET /proxy/network/integration/v1/sites
```
Returns list of all sites (networks) on the controller.

#### Get Devices
```
GET /proxy/network/integration/v1/sites/{site_id}/devices
```
Returns all devices connected to a specific site.

#### Get Device Details
```
GET /proxy/network/integration/v1/sites/{site_id}/devices/{device_id}
```
Returns detailed information about a specific device.

#### Get Network Status
```
GET /proxy/network/integration/v1/sites/{site_id}/network/status
```
Returns network status and statistics.

---

## What We Can Currently Read

### From UniFi API (Read-Only)

- ✅ **Connected Devices**
  - Device list with names and IPs
  - Device types (camera, wired, wireless)
  - Connection status
  - Signal strength (for wireless)

- ✅ **Device Information**
  - MAC addresses
  - Model numbers
  - Firmware versions
  - IP addresses

- ✅ **Network Statistics**
  - Total devices
  - Connected devices count
  - Bandwidth usage
  - Network health status

### From HomeConnect API (Read-Only)

- ✅ **Appliance Status**
  - Power status
  - Temperature settings
  - Door status (fridge)
  - Timer/cycle status (oven)

### From WebOS API (Read-Only)

- ✅ **TV Status**
  - Power state
  - Current input
  - Volume level
  - App information

---

## Current Access Levels

| API | Access Level | Date | Notes |
|---|---|---|---|
| UniFi | Read-only | 2026-05-14 | Full read access, write pending |
| HomeConnect | Read-only | TBD | Will be added in Phase 2 |
| WebOS | Read-only | TBD | Will be added in Phase 3 |

---

## Future Write Access

Once write access is granted:

### Planned UniFi Controls
- [ ] Block/Allow internet for specific devices
- [ ] Temporarily restrict network access
- [ ] Update device names/groups
- [ ] Manage network settings

### Planned HomeConnect Controls
- [ ] Control oven power and temperature
- [ ] Adjust fridge temperature
- [ ] Start/stop cycles

### Planned WebOS Controls
- [ ] Power on/off
- [ ] Change volume
- [ ] Switch inputs
- [ ] Control apps

---

## Network Topology

```
Internet
  |
  └─ UniFi Dream Machine (10.20.40.1)
     |
     ├─ Main Network (10.20.40.0/26)
     |  ├─ Cameras
     |  |  ├─ Garden-kitchen (10.20.40.7)
     |  |  ├─ Main Entrance (10.20.40.22)
     |  |  ├─ Main Door Bell (10.20.40.56)
     |  |  └─ Daisy Entrance (10.20.40.15)
     |  └─ Smart Devices
     |     ├─ Gaggenau Oven 1 (10.20.40.24)
     |     ├─ Gaggenau Oven 2 (10.20.40.5)
     |     ├─ Siemens Fridge (10.20.40.57)
     |     └─ LG TV (10.20.40.59)
     |
     └─ Guest Network (10.20.80.0/27)
        └─ (Empty for now)
```

---

## Integration Timeline

**Phase 1:** UniFi Router Integration (Current)
- Read device list
- Get device status
- Monitor network health

**Phase 2:** HomeConnect Integration
- Read appliance status
- Control oven/fridge

**Phase 3:** LG WebOS Integration
- Read TV status
- Control TV

**Phase 4:** Web Dashboard
- Display all devices
- Control devices from dashboard

**Phase 5:** Docker Deployment
- Deploy to QNAP NAS

---

## Notes

- All devices are on the main network (10.20.40.0/26)
- Guest network is empty for now
- Read-only access is sufficient to start monitoring
- Write access will be requested for device control
- All API communications should be HTTPS (SSL certificate is self-signed)

---

Last Updated: 2026-05-14
