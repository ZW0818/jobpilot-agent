from typing import Any

from utils.path_tool import config_dir


def load_yaml_config(filename: str) -> dict[str, Any]:
    path = config_dir() / filename
    try:
        import yaml
    except ImportError:
        return {}

    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    data = yaml.safe_load(content) or {}
    return data if isinstance(data, dict) else {}
