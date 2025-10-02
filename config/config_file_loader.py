import json
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

class ConfigFileLoader(ABC):
    """Base class for loading a configuration from a file."""

    @abstractmethod
    def load_config(self, config_path: str | Path) -> dict:
        """Load configuration from a file."""
        raise NotImplementedError
    
class ConfigYamlLoader(ConfigFileLoader):
    """Load a configuration from a yaml file."""

    def load_config(self, config_path: str | Path) -> dict:
        
        config_path = Path(config_path)
        if config_path.suffix not in [".yaml", ".yml"]:
            msg = f"Invalid file extension for loading yaml config from: {config_path!s}. Expected .yaml or .yml"
            raise ValueError(msg)
        root_dir = str(config_path.parent)
        if not config_path.is_file():
            msg = f"Config file not found: {config_path}"
            raise FileNotFoundError(msg)
        with config_path.open("rb") as file:
            return yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))