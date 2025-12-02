import os
import sys

# Use tomllib if Python >= 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    tomllib = None  # fallback for older Python


def count_files_by_language(repo_path: str):
    extensions = {
        "Python": [".py"],
        "Java": [".java"],
        "Go": [".go"],
        "JavaScript": [".js"],
        "TypeScript": [".ts"],
        "Kotlin": [".kt"],
        "Groovy": [".groovy"],
        "C": [".c"],
        "C++": [".cpp", ".cc", ".cxx"],
        "C#": [".cs"],
        "Ruby": [".rb"],
        "Rust": [".rs"],
        "PHP": [".php"],
        "Swift": [".swift"],
        "Shell": [".sh"],
        "HTML": [".html"],
        "CSS": [".css"],
        "SQL": [".sql"],
        "JSON": [".json"],
        "YAML": [".yml", ".yaml"],
        "Markdown": [".md"],
    }

    lang_counts = {lang: 0 for lang in extensions}
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
            fname = file.lower()  # normalize for case-insensitive match

            # Special files
            if fname == "dockerfile":
                special_files["Dockerfile"] += 1
            elif fname == ".dockerignore":
                special_files["DockerIgnore"] += 1
            elif fname == ".gitignore":
                special_files["GitIgnore"] += 1
            elif fname == ".editorconfig":
                special_files["EditorConfig"] += 1

            # Language counts
            for lang, exts in extensions.items():
                if any(fname.endswith(ext.lower()) for ext in exts):
                    lang_counts[lang] += 1
                    break  # stop after first matching language

    languages_found = [lang for lang, count in lang_counts.items() if count > 0]

    return lang_counts, total_files, languages_found, special_files


def detect_language(repo_path: str):
    """
    Detects:
      - Language counts
      - Total files
      - Special files (.dockerignore, .gitignore, Dockerfile)
      - Languages found
      - Main detected language
    Returns everything as a dictionary.
    """

    lang_counts, total_files, languages_found, special_files = count_files_by_language(repo_path)

    # Pick primary language
    main_language = max(lang_counts, key=lang_counts.get)
    if lang_counts[main_language] == 0:
        main_language = "Unknown"

    return {
        "language_counts": lang_counts,
        "total_files": total_files,
        "languages_found": languages_found,
        "special_files": special_files,
        "detected_language": main_language
    }


def detect_dependency_manager(repo_path: str, language: str) -> str:
    """
    Auto-detect dependency manager from project files
    """

    manager = "Unknown"

    # -------------------- PYTHON --------------------
    if language == "Python":
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
    if language in ["Java", "Kotlin", "Groovy"]:
        for root, _, files in os.walk(repo_path):
            files_lower = [f.lower() for f in files]
            if "pom.xml" in files_lower:
                return "maven"
            if "build.gradle" in files_lower or "build.gradle.kts" in files_lower:
                return "gradle"

    # -------------------- JAVASCRIPT / TYPESCRIPT --------------------
    if language in ["JavaScript", "TypeScript"]:
        for root, _, files in os.walk(repo_path):
            if "package.json" in [f.lower() for f in files]:
                return "npm / yarn / pnpm"

    # -------------------- GO --------------------
    if language == "Go":
        for root, _, files in os.walk(repo_path):
            if "go.mod" in [f.lower() for f in files]:
                return "go modules"

    # -------------------- RUST --------------------
    if language == "Rust":
        for root, _, files in os.walk(repo_path):
            if "cargo.toml" in [f.lower() for f in files]:
                return "cargo"

    # -------------------- PHP --------------------
    if language == "PHP":
        for root, _, files in os.walk(repo_path):
            if "composer.json" in [f.lower() for f in files]:
                return "composer"

    return manager
