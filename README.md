# ARIA - Automated Residential Intelligence Assistant

## Project Overview

ARIA is a centralized home automation system that provides unified control of multiple IoT devices and network infrastructure from a single web interface. The system is built with a scalable architecture designed to integrate multiple smart home ecosystems.

**Status**: In Development (Learning Project)

---

## System Architecture

The system follows a three-tier architecture:

1. **User Interface Layer**: Web dashboard (and future mobile app) for user interaction
2. **Application Layer**: MCP Server built in Python handling business logic and device coordination
3. **Integration Layer**: Device-specific API adapters for third-party services

Data flows from user actions through the MCP server to device APIs, with status updates returned back to the user interface.

---

## Supported Devices & Integrations

| Device | Category | API | Status |
|--------|----------|-----|--------|
| Ubiquiti Dream Machine / Router | Network | UniFi API | Planned |
| Ubiquiti Doorbell | Security | UniFi API | Planned |
| Siemens Fridge | Appliance | HomeConnect | Planned |
| Geggenau Oven | Appliance | HomeConnect | Planned |
| LG TV | Entertainment | WebOS API | Planned |

---

## Technical Stack

- **Backend**: Python 3.x with MCP (Model Context Protocol) framework
- **Server**: Docker container running on QNAP NAS
- **Frontend**: Web dashboard (HTML/CSS/JavaScript)
- **APIs**: 
  - UniFi API (Ubiquiti devices)
  - HomeConnect API (Siemens/Geggenau appliances)
  - LG WebOS API (LG TV)

---

## Project Goals

- [x] Define architecture and design
- [ ] Set up development environment
- [ ] Implement basic MCP server structure
- [ ] Integrate UniFi API (Phase 1)
- [ ] Integrate HomeConnect API (Phase 2)
- [ ] Integrate LG WebOS API (Phase 3)
- [ ] Build web dashboard
- [ ] Deploy to QNAP
- [ ] (Future) Build Android mobile app

---

## Development Roadmap

**Phase 1**: Core Infrastructure & UniFi Integration
- Set up Python project structure
- Create MCP server skeleton
- Implement Ubiquiti router/doorbell control

**Phase 2**: Smart Appliance Integration
- Integrate HomeConnect API
- Add Fridge and Oven controls

**Phase 3**: Entertainment & Web UI
- Integrate LG WebOS
- Build responsive web dashboard
- Implement real-time status updates

**Phase 4**: Deployment & Polish
- Containerize for QNAP
- Testing and optimization
- Security hardening

---

## Learning Outcomes

This project demonstrates:
- API integration and REST client development
- Microservice architecture design
- Python backend development
- IoT/Smart home system design
- Docker containerization
- Web application frontend development

---

## Future Enhancements

- Android mobile application
- Voice control integration (Alexa/Google Assistant)
- Automation rules and scheduling
- Energy monitoring and optimization
- Security camera integration
- Smart lighting control

---

## License

Personal project - documentation available upon request.
