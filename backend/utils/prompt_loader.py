import json

from pydantic import BaseModel

from utils.path_tool import prompt_dir


def load_prompt(filename: str) -> str:
    path = prompt_dir() / filename
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return "{input}"


def load_structured_prompt(filename: str, schema: type[BaseModel]) -> str:
    return (
        load_prompt(filename)
        + '\nReturn a JSON object that strictly follows the JSON Schema below. '
        + 'Array item types must match the schema: when items are strings, do not return objects. '
        + 'Use "" for unknown string fields and [] for unknown list fields. Do not return null.\n'
        + json.dumps(schema.model_json_schema(), ensure_ascii=False)
    )
