# ARIA Security Requirements Document

**Purpose**: Define security measures for the ARIA home automation system to protect household network and connected devices.

**Prepared for**: Network Manager Review

---

## 1. AUTHENTICATION & ACCESS CONTROL

### 1.1 User Authentication
- [ ] **Username & Password Login** - Required to access ARIA dashboard
  - Minimum 8 character passwords
  - Password hashing (bcrypt or Argon2)
  - Password change required on first login
  
- [ ] **Two-Factor Authentication (2FA)** - Optional but recommended
  - TOTP (Time-based One-Time Password) via authenticator app
  - Email-based verification code
  
- [ ] **Session Management**
  - Session timeout after 30 minutes of inactivity
  - Secure session tokens (JWT or similar)
  - Ability to revoke sessions remotely

### 1.2 API Key Management
- [ ] API keys for programmatic access (for future mobile app)
  - Generated with specific permissions
  - Rate limiting per key
  - Ability to revoke/rotate keys
  - Key expiration dates

---

## 2. NETWORK SECURITY

### 2.1 Communication Encryption
- [ ] **HTTPS/TLS Encryption** - All web traffic encrypted
  - Self-signed certificate (local) or Let's Encrypt (cloud)
  - TLS 1.2 or higher
  - Strong cipher suites

- [ ] **Local Network Only** (Initial Deployment)
  - ARIA only accessible from home network (192.168.x.x)
  - VPN required for remote access (in future phases)

### 2.2 Network Segmentation
- [ ] **Isolated Subnet** (Future Enhancement)
  - ARIA server on separate VLAN/network segment
  - Firewall rules limiting what ARIA can access
  - Separate credentials for device APIs

### 2.3 API Security
- [ ] **Credential Storage**
  - Never hardcode API keys in code
  - Store in encrypted `.env` file (Git ignored)
  - Use environment variables for deployment
  - Rotate credentials regularly

- [ ] **API Rate Limiting**
  - Prevent brute force attacks
  - Limit requests per IP/user
  - Log suspicious activity

---

## 3. DEVICE CONTROL SECURITY

### 3.1 Command Authorization
- [ ] **Permission Levels**
  - Admin: Full control of all devices
  - User: Limited control (e.g., TV, entertainment only)
  - Guest: Read-only access (view status only)

- [ ] **Command Logging**
  - Log EVERY command issued (who, what, when)
  - Log all device state changes
  - Audit trail for investigation

### 3.2 Critical Device Protection
- [ ] **Router/Network Controls** - Extra Protection
  - Require confirmation before allowing internet blocking
  - Whitelist certain devices that cannot be blocked
  - Rate limit network changes (max 5 changes per hour)
  - Notification when network changes occur

- [ ] **Oven/Safety Devices** - Extra Protection
  - Require explicit confirmation before power changes
  - Cannot turn on remotely (only off for safety)
  - Alert on any command execution

---

## 4. DATA PROTECTION

### 4.1 Data Storage
- [ ] **Device Status Data**
  - Minimal data retention (30 days)
  - Encrypted at rest
  - Regular backups

- [ ] **Logs & Audit Trail**
  - Encrypted log storage
  - 90-day retention minimum
  - Immutable (cannot be deleted once written)

### 4.2 Privacy
- [ ] **Sensitive Data Handling**
  - No storage of video feeds (from doorbell)
  - No storage of appliance detailed logs
  - Only store control commands, not results

---

## 5. MONITORING & ALERTING

### 5.1 Security Monitoring
- [ ] **Failed Login Attempts**
  - Alert after 3 failed attempts
  - Account lockout after 5 attempts (15 min)
  - Log all failed attempts with IP address

- [ ] **Unusual Activity Detection**
  - Alert on commands at unusual times
  - Alert on multiple device changes in short time
  - Alert on API errors or timeouts

### 5.2 System Health
- [ ] **Status Monitoring**
  - Check if device connections are active
  - Alert if API connectivity lost
  - Monitor server resource usage (CPU, memory)

- [ ] **Notifications**
  - Email alerts for security events
  - In-app notifications for critical events
  - SMS alerts for security breaches (future)

---

## 6. DEPLOYMENT SECURITY

### 6.1 Docker Container Security
- [ ] **Container Image**
  - Use official base images
  - Minimal dependencies (small attack surface)
  - Regular security updates
  - Container runs as non-root user

- [ ] **QNAP NAS Configuration**
  - Strong QNAP admin password
  - Container network isolation
  - Resource limits (prevent DoS)
  - Regular backups of configuration

### 6.2 Updates & Patching
- [ ] **Dependency Updates**
  - Regular Python package updates
  - Security patch monitoring
  - Automated update notifications

---

## 7. INCIDENT RESPONSE

### 7.1 Security Breach Response
- [ ] **If Unauthorized Access Detected**
  - Automatically revoke all sessions
  - Force password reset on next login
  - Alert network manager immediately
  - Preserve all logs for investigation

- [ ] **If Device Compromised**
  - Disconnect device from ARIA immediately
  - Preserve command logs
  - Investigate unauthorized commands

### 7.2 Recovery Plan
- [ ] **Backup & Restore**
  - Daily automated backups
  - Ability to restore to previous state
  - Test restores monthly

---

## 8. FUTURE ENHANCEMENTS (Phase 2+)

- [ ] **Remote Access via VPN** - Secure tunnel to access from outside
- [ ] **OAuth2 Integration** - Single sign-on (if multi-user)
- [ ] **Hardware Security Keys** - U2F keys instead of phone authenticator
- [ ] **Advanced Threat Detection** - Machine learning for anomaly detection
- [ ] **End-to-End Encryption** - Encrypt commands at source
- [ ] **Hardware Firewall Rules** - Integration with UniFi firewall

---

## 9. COMPLIANCE & STANDARDS

This system should follow:
- [ ] **OWASP Top 10** - Web application security
- [ ] **IoT Security Best Practices** - Device security
- [ ] **Local Data Protection** - Privacy regulations (GDPR if applicable)

---

## 10. INITIAL DEPLOYMENT SECURITY CHECKLIST

**Before deploying to QNAP, verify:**

- [ ] All credentials stored in `.env` (not in code)
- [ ] HTTPS enabled with valid certificate
- [ ] User login required to access dashboard
- [ ] All API communications encrypted
- [ ] Command logging implemented
- [ ] Failed login protection active
- [ ] Network access restricted to home network only
- [ ] Daily backups configured
- [ ] Security alerts configured
- [ ] Documentation complete for network manager

---

## 11. QUESTIONS FOR NETWORK MANAGER (Your Dad)

Ask your dad about:

1. **Network Access**: Should ARIA only work on home network, or remote access later?
2. **Authentication**: 2FA requirement or optional?
3. **Device Permissions**: Should some family members have limited access?
4. **Monitoring**: Any specific monitoring/alerting he wants?
5. **Logging**: How long should logs be kept?
6. **Router Access**: Any limits on what ARIA can do to the router?
7. **Network Changes**: Should he get alerts for network modifications?
8. **Backup**: Backup location/frequency preferences?
9. **Updates**: Auto-update policy for security patches?
10. **Incident Response**: What's the protocol if security issue occurs?

---

## Implementation Priority

**Phase 1 (MVP - Before QNAP Deployment):**
1. Username/password login
2. HTTPS encryption
3. Command logging
4. Failed login protection
5. Local network only access

**Phase 2 (Enhanced Security):**
1. Two-factor authentication
2. Permission levels (admin/user/guest)
3. Advanced monitoring
4. Automated backups

**Phase 3+ (Future):**
1. VPN for remote access
2. OAuth2 integration
3. Hardware security keys
4. Advanced threat detection

---

## Sign-Off

This security plan should be reviewed and approved by the household network manager before ARIA deployment.

**Network Manager**: ________________  **Date**: ________

**ARIA Developer**: ________________  **Date**: ________

