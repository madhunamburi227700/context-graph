import os
import json


def load_dependencies_from_json(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in '{file_path}'")
        return {}
    

def convert_json(json_input, json_output):
    if not os.path.exists(json_input):
        print(f"⚠️ Input file '{json_input}' not found. Skipping normalization.")
        return {}

    raw = load_dependencies_from_json(json_input)

    def normalize(node):
        deps = []
        for key, sub in node.items():
            pkg, ver = key.split("==", 1) if "==" in key else (key, "")
            deps.append({
                "package_name": pkg,
                "installed_version": ver,
                "required_version": "Any",
                "dependencies": normalize(sub) if isinstance(sub, dict) else []
            })
        return deps

    normalized = normalize(raw)

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump({"dependencies": normalized}, f, indent=2)

    print(f"✅ Normalized dependencies saved to {json_output}")
    return normalized
