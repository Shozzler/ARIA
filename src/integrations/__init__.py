"""
ARIA Integrations Module

This module contains integrations with various home automation devices:
- UniFi: Network device management
- HomeConnect: Siemens/Bosch appliances
- WebOS: LG Smart TV
"""

from .unifi import UniFiClient
from .webos_tv import WebOSTVClient

__all__ = ['UniFiClient', 'WebOSTVClient']
