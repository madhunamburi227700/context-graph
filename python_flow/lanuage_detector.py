import os
import sys
import json
from pathlib import Path

# ---------------- tomllib compatibility ----------------
if sys.version_info >= (3, 11):
    import tomllib
else:
    tomllib = None


class LanguageDependencyAnalyzer:
    def __init__(
        self,
        repo_path: str | Path,
        report_file: str | Path,
        orchestration_root: str | Path,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.report_file = Path(report_file)
        self.orchestration_root = Path(orchestration_root)
        self.orchestration_root.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------
    def _write_output(self, message: str):
        with open(self.report_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")

    def _count_files_by_extension(self):
        ext_counts = {}
        total_files = 0

        special_files = {
            "Dockerfile": 0,
            "DockerIgnore": 0,
            "GitIgnore": 0,
            "EditorConfig": 0,
        }

        for root, _, files in os.walk(self.repo_path):
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

                # Extension-based count
                if "." in file:
                    ext = "." + file.lower().split(".")[-1]
                else:
                    ext = "<no_extension>"

                ext_counts[ext] = ext_counts.get(ext, 0) + 1

        ext_counts = dict(sorted(ext_counts.items(), key=lambda x: x[1], reverse=True))
        return ext_counts, total_files, list(ext_counts.keys()), special_files

    # --------------------------------------------------
    # Core logic
    # --------------------------------------------------
    def detect_language(self) -> dict:
        ext_counts, total_files, extensions, special_files = (
            self._count_files_by_extension()
        )

        detected_language = max(ext_counts, key=ext_counts.get) if ext_counts else "Unknown"

        return {
            "language_counts": ext_counts,
            "total_files": total_files,
            "languages_found": extensions,
            "special_files": special_files,
            "detected_language": detected_language,
        }

    def detect_dependency_manager(self, language: str) -> str:
        for root, _, files in os.walk(self.repo_path):
            files_lower = [f.lower() for f in files]

            if language == ".py":
                if "poetry.lock" in files_lower:
                    return "poetry"
                if "requirements.txt" in files_lower:
                    return "pip"
                if "pipfile" in files_lower:
                    return "pipenv"
                if "pyproject.toml" in files_lower:
                    return "pyproject"

            if language in [".java", ".kt", ".groovy"]:
                if "pom.xml" in files_lower:
                    return "maven"
                if "build.gradle" in files_lower:
                    return "gradle"

            if language in [".js", ".ts"] and "package.json" in files_lower:
                return "npm / yarn / pnpm"

            if language == ".go" and "go.mod" in files_lower:
                return "go modules"

            if language == ".rs" and "cargo.toml" in files_lower:
                return "cargo"

            if language == ".php" and "composer.json" in files_lower:
                return "composer"

        return "Unknown"

    # --------------------------------------------------
    # SIMPLE ORCHESTRATION (ONE METHOD)
    # --------------------------------------------------
    def run(self):
        self._write_output(
            "\n----- Section 2.1: Language & Dependency Manager (Windows) -----"
        )

        language_info = self.detect_language()
        detected_language = language_info["detected_language"]

        self._write_output("\n📂 File counts by language:")
        for lang, count in language_info["language_counts"].items():
            self._write_output(f"   - {lang}: {count} files")

        self._write_output("\n🛠 Special files:")
        for k, v in language_info["special_files"].items():
            self._write_output(f"   - {k}: {v}")

        self._write_output(f"\n📄 Total files: {language_info['total_files']}")
        self._write_output(
            f"📌 Languages found: {', '.join(language_info['languages_found'])}"
        )
        self._write_output(
            f"📌 Detected language: {detected_language}"
        )

        dependency_manager = self.detect_dependency_manager(detected_language)
        self._write_output(
            f"📌 Detected dependency manager: {dependency_manager}"
        )

        # Save JSON
        output_data = {
            "repo_path": str(self.repo_path),
            "language_analysis": language_info,
            "dependency_manager": dependency_manager,
        }

        json_path = self.orchestration_root / "repo_analysis.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4)

        self._write_output(
            f"\n📁 Analysis JSON saved at: {json_path}"
        )
        self._write_output(
            "---------------------------------------------------"
        )

        # Next section placeholder
        self._write_output(
            "\n----- Section 3: SBOM Generation (Windows) -----"
        )
