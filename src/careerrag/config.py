"""Store and retrieve settings from the system keychain."""

import keyring

KEYRING_SERVICE = "careerrag"
SETTING_ANTHROPIC_API_KEY = "anthropic_api_key"
SETTING_MODEL = "model"
SETTING_PROVIDER = "provider"


def load_setting(name: str, default: str = "") -> str:
    """Return a setting from the system keychain."""
    return keyring.get_password(KEYRING_SERVICE, name) or default


def save_setting(name: str, value: str) -> None:
    """Store a setting in the system keychain."""
    keyring.set_password(KEYRING_SERVICE, name, value)
