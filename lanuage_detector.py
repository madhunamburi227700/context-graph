import os
import sys
import json

# Use tomllib if Python >= 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    tomllib = None  # fallback for older Python


def count_files_by_language(repo_path: str):
    """
    Count files by extension instead of predefined language mapping.
    Returns:
        ext_counts: dict of {".py": 12, ".js": 8, ...}
        total_files: int
        extensions_found: list of all extensions
        special_files: dict of special files counts
    """
    ext_counts = {}
    total_files = 0

    special_files = {
        "Dockerfile": 0,
        "DockerIgnore": 0,
        "GitIgnore": 0,
        "EditorConfig": 0,
    }

    for root, _, files in os.walk(repo_path):
        for file in files:
            total_files += 1
            fname = file.lower()

            # Special files
            if fname == "dockerfile":
                special_files["Dockerfile"] += 1
            elif fname == ".dockerignore":
                special_files["DockerIgnore"] += 1
            elif fname == ".gitignore":
                special_files["GitIgnore"] += 1
            elif fname == ".editorconfig":
                special_files["EditorConfig"] += 1

            # Extension-based counting
            if "." in file:
                ext = "." + file.lower().split(".")[-1]
            else:
                ext = "<no_extension>"

            ext_counts[ext] = ext_counts.get(ext, 0) + 1

    # Sort by descending count
    ext_counts = dict(sorted(ext_counts.items(), key=lambda x: x[1], reverse=True))
    extensions_found = list(ext_counts.keys())

    return ext_counts, total_files, extensions_found, special_files


def detect_language(repo_path: str):
    """
    Detects:
      - Extension counts (treated as languages)
      - Total files
      - Special files (.dockerignore, .gitignore, Dockerfile)
      - Extensions found
      - Most common extension as main detected language
    Returns everything as a dictionary.
    """
    ext_counts, total_files, extensions_found, special_files = count_files_by_language(repo_path)

    # Pick the most common extension as “main language”
    if ext_counts:
        main_language = max(ext_counts, key=ext_counts.get)
    else:
        main_language = "Unknown"

    return {
        "language_counts": ext_counts,
        "total_files": total_files,
        "languages_found": extensions_found,
        "special_files": special_files,
        "detected_language": main_language
    }


def detect_dependency_manager(repo_path: str, language: str) -> str:
    """
    Auto-detect dependency manager from project files based on language/extension
    """
    manager = "Unknown"

    # -------------------- PYTHON --------------------
    if language in [".py", "Python"]:
        for root, _, files in os.walk(repo_path):
            files_lower = [f.lower() for f in files]

            if "poetry.lock" in files_lower:
                return "poetry"
            if "uv.lock" in files_lower:
                return "uv"
            if "pipfile.lock" in files_lower:
                return "pipenv"

            if "requirements.txt" in files_lower:
                return "pip"
            if "pipfile" in files_lower:
                return "pipenv"
            if "setup.py" in files_lower:
                return "setuptools"

            if "pyproject.toml" in files_lower and tomllib:
                pyproject_file = os.path.join(root, "pyproject.toml")
                try:
                    with open(pyproject_file, "rb") as f:
                        data = tomllib.load(f)
                    tool_keys = data.get("tool", {})
                    if "poetry" in tool_keys:
                        return "poetry"
                    if "uv" in tool_keys:
                        return "uv"
                    if "flit" in tool_keys:
                        return "flit"
                    return "pyproject"
                except Exception:
                    return "pyproject"

    # -------------------- JAVA / KOTLIN / GROOVY (Gradle/Maven) --------------------
    if language in [".java", ".kt", ".groovy", "Java", "Kotlin", "Groovy"]:
        for root, _, files in os.walk(repo_path):
            files_lower = [f.lower() for f in files]
            if "pom.xml" in files_lower:
                return "maven"
            if "build.gradle" in files_lower or "build.gradle.kts" in files_lower:
                return "gradle"

    # -------------------- JAVASCRIPT / TYPESCRIPT --------------------
    if language in [".js", ".ts", "JavaScript", "TypeScript"]:
        for root, _, files in os.walk(repo_path):
            if "package.json" in [f.lower() for f in files]:
                return "npm / yarn / pnpm"

    # -------------------- GO --------------------
    if language in [".go", "Go"]:
        for root, _, files in os.walk(repo_path):
            if "go.mod" in [f.lower() for f in files]:
                return "go modules"

    # -------------------- RUST --------------------
    if language in [".rs", "Rust"]:
        for root, _, files in os.walk(repo_path):
            if "cargo.toml" in [f.lower() for f in files]:
                return "cargo"

    # -------------------- PHP --------------------
    if language in [".php", "PHP"]:
        for root, _, files in os.walk(repo_path):
            if "composer.json" in [f.lower() for f in files]:
                return "composer"

    return manager
