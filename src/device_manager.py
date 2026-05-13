"""
Device Manager Base Class
Handles all device interactions and state management
"""

import logging
from typing import Dict, Any, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Device(ABC):
    """
    Abstract base class for all smart home devices.
    All devices (TV, Fridge, Oven, etc.) will inherit from this.
    """

    def __init__(self, device_id: str, device_name: str, device_type: str):
        """
        Initialize a device.

        Args:
            device_id: Unique identifier for the device
            device_name: Human-readable name (e.g., "Living Room TV")
            device_type: Type of device (e.g., "tv", "fridge", "oven")
        """
        self.device_id = device_id
        self.device_name = device_name
        self.device_type = device_type
        self.is_connected = False
        self.status = {}

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the device. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the device. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current device status. Must be implemented by subclasses."""
        pass

    def __repr__(self):
        return f"Device({self.device_type}, {self.device_name}, connected={self.is_connected})"


class DeviceManager:
    """
    Manages all connected devices.
    Keeps track of device states and routes commands to appropriate devices.
    """

    def __init__(self):
        """Initialize the device manager"""
        self.devices: Dict[str, Device] = {}
        logger.info("Device Manager initialized")

    def register_device(self, device: Device) -> bool:
        """
        Register a new device with the manager.

        Args:
            device: Device object to register

        Returns:
            True if registration successful, False otherwise
        """
        if device.device_id in self.devices:
            logger.warning(f"Device {device.device_id} already registered")
            return False

        self.devices[device.device_id] = device
        logger.info(f"Device registered: {device.device_name} ({device.device_type})")
        return True

    def get_device(self, device_id: str) -> Device:
        """Get a device by ID"""
        return self.devices.get(device_id)

    def get_all_devices(self) -> List[Device]:
        """Get all registered devices"""
        return list(self.devices.values())

    def get_devices_by_type(self, device_type: str) -> List[Device]:
        """Get all devices of a specific type"""
        return [d for d in self.devices.values() if d.device_type == device_type]

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all connected devices.

        Returns:
            Dictionary with device_id as key and status as value
        """
        all_status = {}
        for device_id, device in self.devices.items():
            if device.is_connected:
                all_status[device_id] = device.get_status()
            else:
                all_status[device_id] = {"error": "Device not connected"}
        return all_status

    def __repr__(self):
        return f"DeviceManager(devices={len(self.devices)})"
