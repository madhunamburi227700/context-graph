import os
import re
import subprocess
from pathlib import Path
import platform

# === Detect OS and select correct Gradle wrapper ===
IS_WINDOWS = platform.system().lower().startswith("win")
GRADLEW = "gradlew.bat" if IS_WINDOWS else "./gradlew"

# === File constants ===
OUTPUT_FILE = "gradle_dependencies_command.txt"
ALL_DEP_TREE = "1.txt"
BATCH_SIZE = 50  # number of modules per Gradle run


def parse_settings_gradle(path: Path):
    """Parse includeBuild and include statements from settings.gradle"""
    include_builds = []
    includes = []

    if not path.exists():
        return [], []

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return [], []

    # Remove comments
    content = re.sub(r"//.*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.S)

    # includeBuild 'xyz'
    include_builds += re.findall(r"includeBuild\s+['\"]([^'\"]+)['\"]", content)

    # include 'a:b', 'b:c'
    include_blocks = re.findall(
        r"include\s+(?:['\"][^'\"]+['\"].*?)(?=\n\S|$)", content, flags=re.S
    )
    for block in include_blocks:
        includes += re.findall(r"['\"]([^'\"]+)['\"]", block)

    return include_builds, includes


def has_build_file(folder: Path):
    """Check if folder has a Gradle build file"""
    if not folder.exists() or not folder.is_dir():
        return False
    for file in folder.iterdir():
        if file.name in ("build.gradle", "build.gradle.kts"):
            return True
    return False


def find_all_modules(base_dir: Path, prefix=""):
    """Recursively find all Gradle modules"""
    modules = []
    settings_path = base_dir / "settings.gradle"
    include_builds, includes = parse_settings_gradle(settings_path)

    # Case 1: Only root project
    if prefix == "" and not includes and not include_builds:
        if has_build_file(base_dir):
            modules.append(":")
        return modules

    # Case 2: Regular modules
    for inc in includes:
        module_name = inc.strip(":")
        modules.append(f":{prefix}{module_name}" if prefix else f":{module_name}")

    # Case 3: includeBuild modules
    for build in include_builds:
        build_dir = base_dir / build
        if build_dir.exists():
            sub_prefix = f"{build}:" if not prefix else f"{prefix}{build}:"
            modules += find_all_modules(build_dir, sub_prefix)
        elif has_build_file(build_dir):
            modules.append(f":{prefix}{build}" if prefix else f":{build}")

    # Case 4: A folder with build.gradle but no includes
    if has_build_file(base_dir) and not includes and not include_builds:
        module_name = prefix.rstrip(":")
        modules.append(f":{module_name}" if module_name else ":")

    return modules


def run_gradle_command(modules, batch_num, repo_path: Path):
    """Run Gradle dependencies command for a batch of modules"""
    cmd_parts = [GRADLEW]
    for m in modules:
        cmd_parts.append("dependencies" if m == ":" else f"{m}:dependencies")

    cmd = " ".join(cmd_parts)

    print(f"\n⚙️ Running Gradle batch {batch_num} ({len(modules)} modules)...")

    result = subprocess.run(
        cmd,
        shell=True,
        cwd=repo_path,          # <-- RUN INSIDE REPO
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )

    # Save output into repo folder
    out_file = repo_path / ALL_DEP_TREE
    with open(out_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n========== Batch {batch_num} ==========\n")
        f.write("Command:\n")
        f.write(cmd + "\n\n")
        f.write(result.stdout)
        f.write("\n=======================================\n")

    print(f"✅ Batch {batch_num} complete.")

def generate_gradle_dependency_tree(repo_path):
    """Scan Gradle modules and generate dependency tree inside repo"""

    repo_path = Path(repo_path).resolve()   # Ensure Path

    print("🔍 Scanning recursively for Gradle modules...")

    modules = find_all_modules(repo_path)
    modules = sorted(set(modules))

    print(f"✅ Found {len(modules)} modules:")
    for m in modules:
        print("   ", m)

    # --- Save full Gradle command ---
    out_file = repo_path / OUTPUT_FILE
    full_command = GRADLEW + " " + " ".join(
        ["dependencies" if m == ":" else f"{m}:dependencies" for m in modules]
    )

    out_file.write_text(full_command + "\n", encoding="utf-8")
    print(f"\n🧩 Full Gradle command saved to: {out_file}")

    # --- Initialize dependency output file ---
    dep_file = repo_path / ALL_DEP_TREE
    dep_file.write_text(
        "Full Gradle Dependency Output\n==============================\n",
        encoding="utf-8"
    )

    print(f"📦 Running Gradle in batches of {BATCH_SIZE} modules...\n")

    # --- Run Gradle in batches ---
    for i in range(0, len(modules), BATCH_SIZE):
        batch = modules[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        run_gradle_command(batch, batch_num, repo_path)

    print("\n✅ All batches complete.")
    print(f"📄 Full dependency tree saved at: {dep_file}")

