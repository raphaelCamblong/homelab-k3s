import json
import logging
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional, Union
from enum import Enum

# For TP-Link Kasa devices
from kasa import Discover, SmartDevice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart-device-controller")


class DeviceError(Exception):
    """Base exception for device-related errors."""

    pass


class ActionError(Exception):
    """Exception for invalid actions."""

    pass


class DeviceAction(Enum):
    """Available device actions."""

    LIST = "get_device_list"
    TOGGLE = "toggle_device"
    SET_STATE = "set_device_state"
    TOGGLE_STATIC = "toggle_device_static"
    GET_DEVICE = "get_device"

    @classmethod
    def list_actions(cls) -> List[str]:
        """Get list of available actions."""
        return [action.value for action in cls]


class KasaDeviceManager:
    """Manages TP-Link Kasa smart devices."""

    def __init__(self, discovery_timeout: int = 5):
        """Initialize the Kasa device manager.

        Args:
            discovery_timeout (int): Timeout for device discovery in seconds
        """
        self.discovery_timeout = discovery_timeout

    async def discover_devices(self, target: Optional[str] = None) -> Dict[str, Any]:
        """Discover Kasa devices on the network.

        Args:
            target (Optional[str]): Optional target IP or subnet for discovery

        Returns:
            Dict[str, Any]: Dictionary of discovered devices

        Raises:
            DeviceError: If discovery fails
        """
        try:
            return await Discover.discover(
                target=target, timeout=self.discovery_timeout
            )
        except Exception as e:
            raise DeviceError(f"Error discovering devices: {str(e)}")

    async def get_device_list(self) -> List[Dict[str, Any]]:
        """Get a list of all Kasa devices with their status.

        Returns:
            List[Dict[str, Any]]: List of devices with their properties
        """
        try:
            devices = await self.discover_devices()
            device_list = []

            for addr, dev in devices.items():
                device_list.append((addr, dev.__dict__))

            return device_list
        except Exception as e:
            logger.error(f"Error getting device list: {str(e)}")
            return [{"error": str(e)}]

    async def get_device(self, ip_address: str) -> SmartDevice:
        """Get a specific device by IP address.

        Args:
            ip_address (str): The IP address of the device

        Returns:
            SmartDevice: The device if found

        Raises:
            DeviceError: If device not found or error occurs
        """
        try:
            devices = await self.discover_devices(target=ip_address)
            if ip_address not in devices:
                raise DeviceError(f"Device not found at {ip_address}")

            device = devices[ip_address]
            await device.update()
            return device
        except Exception as e:
            raise DeviceError(f"Error getting device {ip_address}: {str(e)}")

    async def _execute_device_action(
        self, ip_address: str, action: callable, *args
    ) -> Dict[str, Any]:
        """Execute an action on a device with error handling.

        Args:
            ip_address (str): Device IP address
            action (callable): Action to execute
            *args: Arguments for the action

        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            device = await self.get_device(ip_address)
            return await action(device, *args)
        except DeviceError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error executing action on device {ip_address}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def toggle_device(self, ip_address: str) -> Dict[str, Any]:
        """Toggle the power state of a device."""

        async def toggle_action(device: SmartDevice) -> Dict[str, Any]:
            previous_state = device.is_on
            if previous_state:
                await device.turn_off()
            else:
                await device.turn_on()
            return {
                "success": True,
                "device": ip_address,
                "previous_state": previous_state,
                "new_state": not previous_state,
            }

        return await self._execute_device_action(ip_address, toggle_action)

    async def set_device_state(
        self, ip_address: str, power_state: bool
    ) -> Dict[str, Any]:
        """Set a device to a specific power state."""

        async def set_state_action(device: SmartDevice) -> Dict[str, Any]:
            previous_state = device.is_on
            if power_state:
                await device.turn_on()
            else:
                await device.turn_off()
            return {
                "success": True,
                "device": ip_address,
                "previous_state": previous_state,
                "new_state": power_state,
            }

        return await self._execute_device_action(ip_address, set_state_action)


class RequestHandler:
    """Handles incoming requests and routes them to appropriate handlers."""

    def __init__(self):
        self.kasa_manager = KasaDeviceManager()

    def _validate_ip_address(self, request_data: Dict[str, Any]) -> str:
        """Validate and return IP address from request data."""
        ip_address = request_data.get("ip_address")
        if not ip_address:
            raise ActionError("IP address is required")
        return ip_address

    async def handle_discover(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle device discovery request."""
        devices = await self.kasa_manager.discover_devices(request_data.get("target"))
        return {"devices": {k: v.model for k, v in devices.items()}}

    async def handle_device_list(self, _: Dict[str, Any]) -> Dict[str, Any]:
        """Handle device list request."""
        device_list = await self.kasa_manager.get_device_list()
        return {"devices": device_list}

    async def handle_get_device(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get device request."""
        ip_address = request_data.get("ip_address", "")
        return await self.kasa_manager.get_device(ip_address)

    async def handle_toggle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle device toggle request."""
        ip_address = self._validate_ip_address(request_data)
        return await self.kasa_manager.toggle_device(ip_address)

    async def handle_set_state(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle set device state request."""
        ip_address = self._validate_ip_address(request_data)
        power_state = request_data.get("power_state")
        if power_state is None:
            raise ActionError("Power state is required")
        return await self.kasa_manager.set_device_state(ip_address, bool(power_state))

    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the incoming request based on action type."""
        try:
            action = request_data.get("action", "")

            # Map actions to handlers
            handlers = {
                DeviceAction.DISCOVER.value: self.handle_discover,
                DeviceAction.LIST.value: self.handle_device_list,
                DeviceAction.TOGGLE.value: self.handle_toggle,
                DeviceAction.SET_STATE.value: self.handle_set_state,
                DeviceAction.GET_DEVICE.value: self.handle_get_device,
            }

            handler = handlers.get(action)
            if not handler:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": DeviceAction.list_actions(),
                }

            return await handler(request_data)

        except ActionError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {"success": False, "error": str(e)}


def parse_request(event):
    """Parse the request data from the event.

    Args:
        event (dict): The OpenFaaS event object

    Returns:
        dict: Parsed request data with at least an 'action' key
    """
    default_action = ""

    try:
        if event.body:
            return json.loads(event.body)
        return {"action": default_action}
    except json.JSONDecodeError:
        return {"action": default_action}


def handle(event, context) -> str:
    """Handle incoming requests to the function.

    Args:
        req (str): Request body
        context (Any): Context information

    Returns:
        str: JSON response
    """
    try:
        request_data = parse_request(event)
        handler = RequestHandler()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(handler.process_request(request_data))
        except asyncio.CancelledError:
            logger.warning("Async operation was cancelled (likely a timeout)")
            result = {"success": False, "error": "Operation timed out or was cancelled"}
        except Exception as e:
            logger.error(f"Error in async operation: {str(e)}")
            result = {"success": False, "error": str(e)}
        finally:
            loop.close()

        return json.dumps(result)

    except json.JSONDecodeError:
        return json.dumps({"success": False, "error": "Invalid JSON in request"})
    except BaseException as e:
        logger.error(f"Critical error processing request: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})
