# handler.py
import json
import logging
import os
from .ilo_redfish_controller import IloRedfishClient

# Suppress only the single InsecureRequestWarning
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""

    pass


def get_config():
    """Get and validate configuration from environment variables.

    Returns:
        tuple: (host, username, password)

    Raises:
        ConfigurationError: If any required configuration is missing
    """
    config = {
        "host": os.environ.get("ILO_HOST"),
        "username": os.environ.get("ILO_USERNAME"),
        "password": os.environ.get("ILO_PASSWORD"),
    }

    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ConfigurationError(
            f"Missing required configuration: {', '.join(missing)}"
        )

    return config["host"], config["username"], config["password"]


def parse_request(event):
    """Parse the request data from the event.

    Args:
        event (dict): The OpenFaaS event object

    Returns:
        dict: Parsed request data with at least an 'action' key
    """
    default_action = "system_info"

    try:
        if event.body:
            return json.loads(event.body)
        return {"action": default_action}
    except json.JSONDecodeError:
        return {"action": default_action}


def handle_power_control(client, request_data):
    """Handle power control action.

    Args:
        client (IloRedfishClient): The client instance
        request_data (dict): The request data

    Returns:
        dict: Result of the power control operation
    """
    power_action = request_data.get("power_action")
    if not power_action:
        return {"error": "Missing power_action parameter"}
    return client.set_power_state(power_action)


# Action mapping to avoid long if-elif chain
ACTION_HANDLERS = {
    "system_info": lambda client, _: client.get_system_info(),
    "thermal": lambda client, _: client.get_thermal_info(),
    "power": lambda client, _: client.get_power_info(),
    "power_state": lambda client, _: client.get_power_state(),
    "power_control": handle_power_control,
}


def handle(event, context):
    """Handle incoming requests to the function.

    Args:
        event (dict): OpenFaaS event containing request data (body, headers, method, query, path)
        context (dict): Context information about the function

    Returns:
        str: JSON response with requested information
    """
    try:
        # Get and validate configuration
        ilo_host, ilo_username, ilo_password = get_config()
        logger.info(event)

        request_data = parse_request(event)
        client = IloRedfishClient(ilo_host, ilo_username, ilo_password)

        action = request_data.get("action", "system_info")
        handler = ACTION_HANDLERS.get(action)

        if not handler:
            result = {"error": f"Unknown action: {action}"}
        else:
            result = handler(client, request_data)

        return json.dumps(result)

    except ConfigurationError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"})
