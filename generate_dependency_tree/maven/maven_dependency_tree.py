import shutil
import subprocess
import platform
from pathlib import Path
import json
import re

# ----------------------------
# Maven detection
# ----------------------------
def get_mvn_path() -> Path:
    mvn_bin = "mvn.cmd" if platform.system() == "Windows" else "mvn"
    mvn_path = shutil.which(mvn_bin)

    if not mvn_path:
        raise FileNotFoundError(
            f"❌ Maven not found on PATH. Please install Maven and ensure '{mvn_bin}' is available."
        )

    result = subprocess.run([mvn_path, "-v"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"❌ Maven found at {mvn_path} but failed to run.")

    print(f"✅ Using system Maven: {mvn_path}")
    print(result.stdout.splitlines()[0])
    return Path(mvn_path)


# ----------------------------
# Dependency parser
# ----------------------------
DEP_LINE_RE = re.compile(r'^\s*[\|\s\\+]*[\\+]-\s+(.+)$')
DEP_PREFIX_RE = re.compile(r'^(\s*[\|\s\\+]*?)[\\+]-')

def parse_gradle_dependencies(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ File '{file_path}' not found.")
        return {"configurations": []}

    configurations = []
    current_config = None
    stack = []

    def create_dependency(notation_line):
        parts = notation_line.strip().split(':')
        dep = {}
        if len(parts) >= 5:
            dep["group"], dep["name"], dep["type"], dep["version"], dep["scope"] = [p.strip() for p in parts[:5]]
        elif len(parts) == 4:
            dep["group"], dep["name"], dep["type"], dep["version"] = [p.strip() for p in parts[:4]]
        elif len(parts) == 3:
            dep["group"], dep["name"], dep["version"] = [p.strip() for p in parts[:3]]
        else:
            dep["name"] = notation_line.strip()
        dep["dependencies"] = []
        return dep

    def get_depth(line):
        m = DEP_PREFIX_RE.match(line)
        if not m:
            return 0
        prefix = m.group(1)
        cleaned = re.sub(r'[|+]', '', prefix)
        spaces = len(cleaned)
        return spaces // 2

    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped and not stripped.startswith(('+', '|', '\\')):
            top_dep = create_dependency(stripped)
            configurations.append(top_dep)
            current_config = top_dep
            stack.clear()
            continue

        m = DEP_LINE_RE.match(raw_line)
        if not m or current_config is None:
            continue

        notation = m.group(1).strip()
        dep = create_dependency(notation)
        if not dep:
            continue

        depth = get_depth(raw_line)
        while stack and stack[-1]["depth"] >= depth:
            stack.pop()

        if stack:
            parent = stack[-1]["node"]
            parent["dependencies"].append(dep)
        else:
            current_config["dependencies"].append(dep)

        stack.append({"depth": depth, "node": dep})

    return {"configurations": configurations}


def save_dependencies_to_json(parsed_data, output_file):
    try:
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2)
        print(f"✅ Dependencies JSON saved to {output_file}")
    except Exception as e:
        print(f"❌ Error writing JSON: {e}")


# ----------------------------
# Main: scan repo and generate indexed outputs in repo root
# ----------------------------
def generate_maven_dependency_tree(repo_path, output_root):
    repo_path = Path(repo_path).resolve()
    output_root = Path(output_root).resolve()

    print("\n🔍 Checking for Maven projects...")

    # ✅ STEP 1: Detect pom.xml FIRST
    pom_files = list(repo_path.rglob("pom.xml"))
    if not pom_files:
        print("⏭️ No pom.xml found — skipping Maven dependency tree.")
        return False

    # ✅ STEP 2: Resolve Maven ONLY if needed
    try:
        mvn = get_mvn_path()
    except Exception as e:
        print(str(e))
        print("⏭️ Skipping Maven dependency tree.")
        return False

    print(f"🔍 Found {len(pom_files)} pom.xml file(s).")

    # ✅ STEP 3: Process each Maven module
    for idx, pom in enumerate(pom_files, start=1):
        module_dir = pom.parent
        print(f"\n📦 Processing Maven module #{idx}: {module_dir}")

        output_txt = output_root / f"dependency_tree_{idx}.txt"

        result = subprocess.run(
            [
                str(mvn),
                "dependency:tree",
                f"-DoutputFile={output_txt}",
                "-DoutputType=text"
            ],
            cwd=module_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Maven failed for {module_dir}")
            print(result.stderr)
            continue

        print(f"✅ Maven dependency tree saved → {output_txt}")

        # ✅ Parse and save JSON only if TXT exists
        try:
            parsed = parse_gradle_dependencies(output_txt)
            output_json = output_root / f"maven_dependency_tree_{idx}.json"
            save_dependencies_to_json(parsed, output_json)
        except Exception as e:
            print(f"❌ Failed to parse Maven output for {module_dir}: {e}")

    return True
