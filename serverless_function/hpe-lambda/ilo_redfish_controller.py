import logging
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


@dataclass
class RedfishEndpoints:
    """Redfish API endpoints."""

    SYSTEMS = "/Systems"
    CHASSIS = "/Chassis"
    THERMAL = "/Thermal"
    POWER = "/Power"
    RESET_ACTION = "/Actions/ComputerSystem.Reset"


class RedfishError(Exception):
    """Base exception for Redfish API errors."""

    pass


class IloRedfishClient:
    """Client for interacting with HPE iLO Redfish API."""

    VALID_POWER_ACTIONS = [
        "On",
        "ForceOff",
        "GracefulShutdown",
        "ForceRestart",
        "PushPowerButton",
    ]

    def __init__(self, host: str, username: str, password: str):
        """Initialize Redfish client with connection details.

        Args:
            host (str): iLO hostname or IP address
            username (str): iLO username
            password (str): iLO password
        """
        self.base_url = f"https://{host}/redfish/v1"
        self.auth = (username, password)
        self.session = requests.Session()
        self.headers = {"Content-Type": "application/json"}

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Redfish API.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            **kwargs: Additional arguments to pass to requests

        Returns:
            dict: Response data

        Raises:
            RedfishError: If the request fails
        """
        try:
            url = urljoin(self.base_url, endpoint.lstrip("/"))
            response = self.session.request(
                method,
                url,
                auth=self.auth,
                verify=False,
                headers=self.headers,
                **kwargs,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            raise RedfishError(f"API request failed: {str(e)}")

    def _get_first_member_url(self, collection_endpoint: str) -> str:
        """Get the URL of the first member in a collection.

        Args:
            collection_endpoint (str): Collection endpoint path

        Returns:
            str: URL of the first member

        Raises:
            RedfishError: If no members found
        """
        data = self._make_request("GET", collection_endpoint)
        if not data.get("Members"):
            raise RedfishError(f"No members found in {collection_endpoint}")
        return data["Members"][0]["@odata.id"]

    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information.

        Returns:
            dict: System information
        """
        try:
            system_url = self._get_first_member_url(RedfishEndpoints.SYSTEMS)
            return self._make_request("GET", system_url)
        except RedfishError as e:
            return {"error": str(e)}

    def get_thermal_info(self) -> Dict[str, Any]:
        """Get thermal information (temperatures, fans).

        Returns:
            dict: Thermal information
        """
        try:
            chassis_url = self._get_first_member_url(RedfishEndpoints.CHASSIS)
            thermal_url = f"{chassis_url}{RedfishEndpoints.THERMAL}"
            return self._make_request("GET", thermal_url)
        except RedfishError as e:
            return {"error": str(e)}

    def get_power_info(self) -> Dict[str, Any]:
        """Get power information.

        Returns:
            dict: Power information
        """
        try:
            chassis_url = self._get_first_member_url(RedfishEndpoints.CHASSIS)
            power_url = f"{chassis_url}{RedfishEndpoints.POWER}"
            return self._make_request("GET", power_url)
        except RedfishError as e:
            return {"error": str(e)}

    def get_power_state(self) -> Dict[str, Any]:
        """Get the current power state of the server.

        Returns:
            dict: Power state information
        """
        try:
            system_info = self.get_system_info()
            if "error" in system_info:
                return system_info
            return {"PowerState": system_info.get("PowerState", "Unknown")}
        except RedfishError as e:
            return {"error": str(e)}

    def set_power_state(self, power_action: str) -> Dict[str, Any]:
        """Set the power state of the server.

        Args:
            power_action (str): The power action to perform.
                              Valid values: "On", "ForceOff", "GracefulShutdown", "ForceRestart", "PushPowerButton"

        Returns:
            dict: Result of the power action request
        """
        if power_action not in self.VALID_POWER_ACTIONS:
            return {
                "error": f"Invalid power action: {power_action}. Valid actions are: {', '.join(self.VALID_POWER_ACTIONS)}"
            }

        try:
            system_url = self._get_first_member_url(RedfishEndpoints.SYSTEMS)
            reset_url = f"{system_url}{RedfishEndpoints.RESET_ACTION}"
            response = self._make_request(
                "POST", reset_url, json={"ResetType": power_action}
            )
            return {"success": f"Power action '{power_action}' initiated successfully"}
        except RedfishError as e:
            return {"error": str(e)}