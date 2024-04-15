import os
import json
from pathlib import Path

resource_file = Path(os.path.dirname(__file__))


with open(resource_file / "props_library.json", "r", encoding="utf8") as f:
    props_library: dict = json.load(f)


def func(data: dict) -> dict:
    prop = {}
    prop["prop_name"] = data.get("name", "未知")
    prop["color"] = data.get("color", "#000000").upper()
    prop["intro"] = data.get("intro", "无")
    prop["tip"] = data.get("tip", "无")
    return prop


def recode(code: str):
    rare = int(code[0])
    domain = int(code[1]) - 1
    flow = int(code[2])
    number = int(code[3:])
    return f"{rare}{domain}{flow}{number}"


props_dict = {recode(code): func(prop_data) for code, prop_data in props_library.items()}

with open(resource_file / "props_library.json", "w", encoding="utf-8") as f:
    json.dump(props_dict, f, indent=4, ensure_ascii=False)
