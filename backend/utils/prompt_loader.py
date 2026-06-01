from utils.path_tool import prompt_dir


def load_prompt(filename: str) -> str:
    path = prompt_dir() / filename
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return "{input}"
