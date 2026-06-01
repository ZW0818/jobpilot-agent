from pathlib import Path


def backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def prompt_dir() -> Path:
    return backend_root() / "prompts"


def config_dir() -> Path:
    return backend_root() / "config"
