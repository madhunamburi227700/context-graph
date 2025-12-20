import os
import json
import subprocess
from pathlib import Path
from .nodejs_json_format import parse_pnpm_tree


def run_cmd(cmd, cwd, output_file=None):
    print(f"▶ Running: {cmd} (in {cwd})")

    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(result.stderr)
        return False

    if output_file:
        output_file.write_text(result.stdout, encoding="utf-8")

    return True


def find_package_json_dirs(repo_root):
    package_dirs = []

    for root, dirs, files in os.walk(repo_root):
        if "node_modules" in dirs:
            dirs.remove("node_modules")

        if "package.json" in files:
            package_dirs.append(Path(root))

    return package_dirs


def save_tree_json(tree, output_file: Path):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2)
    print(f"📄 Dependency tree JSON saved → {output_file}")


def generate_dependency_trees(repo_root, output_root):
    """
    Detect Node.js projects and generate dependency trees using pnpm.
    Returns True if at least one Node project is processed, else False.
    """
    repo_root = Path(repo_root).resolve()
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    print("\n🔍 Checking for Node.js projects...")

    package_dirs = find_package_json_dirs(repo_root)

    if not package_dirs:
        print("⏭️ No package.json found — skipping Node.js dependency analysis.")
        return False

    print(f"✅ Found {len(package_dirs)} Node.js project(s).")

    output_index = 1

    for pkg_dir in package_dirs:
        print(f"\n📦 Processing Node project: {pkg_dir.relative_to(repo_root)}")

        # 1️⃣ Install dependencies
        if not run_cmd("pnpm install", cwd=pkg_dir):
            print("⏭️ Skipping dependency tree due to install failure.")
            continue

        # 2️⃣ Generate TXT tree
        txt_file = output_root / f"node_dependency_tree_{output_index}.txt"
        if not run_cmd("pnpm list --depth Infinity", cwd=pkg_dir, output_file=txt_file):
            print("⏭️ Dependency tree generation failed.")
            continue

        print(f"📄 Dependency tree saved → {txt_file}")

        # 3️⃣ Convert TXT → JSON
        try:
            tree = parse_pnpm_tree(txt_file)
            json_file = output_root / f"node_dependency_tree_{output_index}.json"
            save_tree_json(tree, json_file)
        except Exception as e:
            print(f"⚠️ Failed to convert dependency tree to JSON: {e}")

        output_index += 1

    return output_index > 1
