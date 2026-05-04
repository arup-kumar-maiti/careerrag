"""Load and save application configuration."""

from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(".careerrag")
CONFIG_FILE = CONFIG_DIR / "config.yml"
DEFAULT_CONFIG = {
    "diversity_enabled": True,
    "host": "127.0.0.1",
    "keyword_enabled": True,
    "model": "llama3.2",
    "ollama_url": "http://localhost:11434/api/chat",
    "port": 8000,
    "provider": "ollama",
    "rerank_enabled": False,
    "store": ".careerrag/store",
}


def save_config(config: dict[str, Any]) -> None:
    """Write the configuration to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        yaml.dump(data=config, default_flow_style=False, sort_keys=True),
        encoding="utf-8",
    )


def load_config() -> dict[str, Any]:
    """Return the configuration with defaults for any missing keys."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError("Configuration not found. Run 'careerrag init'.")
    user_config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    return {**DEFAULT_CONFIG, **user_config}
