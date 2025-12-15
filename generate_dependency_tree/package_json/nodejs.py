import os
import subprocess
from pathlib import Path


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


def generate_dependency_trees(repo_root, output_root):
    """
    repo_root: path returned by clone_and_checkout
    """
    repo_root = Path(repo_root).resolve()
    output_root = Path(output_root).resolve()

    output_index = 1

    print(f"📁 Repo root: {repo_root}")

    package_dirs = find_package_json_dirs(repo_root)

    if not package_dirs:
        print("⚠ No package.json found in repo")
        return

    print(f"✅ Found {len(package_dirs)} package.json folders")

    for pkg_dir in package_dirs:
        print(f"\n📦 Processing folder: {pkg_dir.relative_to(repo_root)}")

        run_cmd("pnpm install", cwd=pkg_dir)

        output_file = output_root / f"dependency_tree_{output_index}.txt"
        run_cmd(
            "pnpm list --depth Infinity",
            cwd=pkg_dir,
            output_file=output_file
        )

        print(f"📄 Saved: {output_file.name}")
        output_index += 1
