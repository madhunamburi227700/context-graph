import json
import re
from pathlib import Path


def parse_pnpm_tree(txt_file: Path):
    root = {"name": "root", "dependencies": []}
    stack = [(-1, root)]

    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            depth = len(re.findall(r"[│├└]", line))
            clean = re.sub(r"[│├└─┬]", "", line).strip()

            if "@" not in clean:
                continue

            name_version = clean.split(" ", 1)[0]
            name, version = name_version.rsplit("@", 1)

            node = {
                "name": name,
                "version": version,
                "dependencies": []
            }

            while stack and stack[-1][0] >= depth:
                stack.pop()

            stack[-1][1]["dependencies"].append(node)
            stack.append((depth, node))

    return root
