import os
import re
import subprocess
from pathlib import Path
import platform

class GradleDependencyHandler:
    IS_WINDOWS = platform.system().lower().startswith("win")
    GRADLEW = "gradlew.bat" if IS_WINDOWS else "./gradlew"

    OUTPUT_FILE = "gradle_dependencies_command.txt"
    ALL_DEP_TREE = "1.txt"
    BATCH_SIZE = 50  # number of modules per Gradle run

    def __init__(self, repo_path: Path, output_root: Path, report_file: Path):
        self.repo_path = Path(repo_path).resolve()
        self.output_root = Path(output_root).resolve()
        self.report_file = Path(report_file)

    # ---------------- Internal helpers ----------------
    def _write_report(self, text: str):
        with open(self.report_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    @staticmethod
    def _parse_settings_gradle(path: Path):
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

        include_builds += re.findall(r"includeBuild\s+['\"]([^'\"]+)['\"]", content)
        include_blocks = re.findall(r"include\s+(?:['\"][^'\"]+['\"].*?)(?=\n\S|$)", content, flags=re.S)
        for block in include_blocks:
            includes += re.findall(r"['\"]([^'\"]+)['\"]", block)

        return include_builds, includes

    @staticmethod
    def _has_build_file(folder: Path):
        if not folder.exists() or not folder.is_dir():
            return False
        return any(file.name in ("build.gradle", "build.gradle.kts") for file in folder.iterdir())

    def _find_all_modules(self, base_dir: Path = None, prefix=""):
        base_dir = base_dir or self.repo_path
        modules = []
        settings_path = base_dir / "settings.gradle"
        include_builds, includes = self._parse_settings_gradle(settings_path)

        if prefix == "" and not includes and not include_builds:
            if self._has_build_file(base_dir):
                modules.append(":")
            return modules

        # Regular includes
        for inc in includes:
            module_name = inc.strip(":")
            modules.append(f":{prefix}{module_name}" if prefix else f":{module_name}")

        # includeBuild modules
        for build in include_builds:
            build_dir = base_dir / build
            if build_dir.exists():
                sub_prefix = f"{build}:" if not prefix else f"{prefix}{build}:"
                modules += self._find_all_modules(build_dir, sub_prefix)
            elif self._has_build_file(build_dir):
                modules.append(f":{prefix}{build}" if prefix else f":{build}")

        # Folder with build.gradle but no includes
        if self._has_build_file(base_dir) and not includes and not include_builds:
            module_name = prefix.rstrip(":")
            modules.append(f":{module_name}" if module_name else ":")

        return modules

    def _detect_gradle(self):
        return any(self.repo_path.rglob(pattern) for pattern in ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"])

    def _run_gradle_command(self, modules, batch_num):
        cmd_parts = [self.GRADLEW] + [
            "dependencies" if m == ":" else f"{m}:dependencies" for m in modules
        ]
        cmd = " ".join(cmd_parts)
        # self._write_report(f"\n⚙️ Running Gradle batch {batch_num} ({len(modules)} modules)...")

        result = subprocess.run(
            cmd,
            shell=True,
            cwd=self.repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        # Append Gradle output to 1.txt
        out_file = self.output_root / self.ALL_DEP_TREE
        with open(out_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n========== Batch {batch_num} ==========\n")
            f.write("Command:\n")
            f.write(cmd + "\n\n")
            f.write(result.stdout)
            f.write("\n=======================================\n")

        # self._write_report(f"✅ Batch {batch_num} complete.")

    # ---------------- Public method ----------------
    def run(self) -> bool:
        self._write_report("\n-----Section 5.3: Gradle Projects-----")

        if not self._detect_gradle():
            # self._write_report("⏭️ No Gradle project found — skipping dependency tree.")
            return False

        self._write_report("✅ Gradle project detected. Scanning modules...")
        modules = sorted(set(self._find_all_modules()))
        if not modules:
            self._write_report("⏭️ No Gradle modules resolved — skipping.")
            return False

        # self._write_report(f"✅ Found {len(modules)} modules:")
        # for m in modules:
        #     self._write_report(f"   {m}")

        # Save full Gradle command
        out_file = self.output_root / self.OUTPUT_FILE
        full_command = self.GRADLEW + " " + " ".join(
            ["dependencies" if m == ":" else f"{m}:dependencies" for m in modules]
        )
        out_file.write_text(full_command + "\n", encoding="utf-8")
        # self._write_report(f"\n🧩 Full Gradle command saved to: {out_file}")

        # Initialize dependency output file
        dep_file = self.output_root / self.ALL_DEP_TREE
        dep_file.write_text("Full Gradle Dependency Output\n==============================\n", encoding="utf-8")

        # Run Gradle in batches
        for i in range(0, len(modules), self.BATCH_SIZE):
            batch = modules[i: i + self.BATCH_SIZE]
            batch_num = (i // self.BATCH_SIZE) + 1
            self._run_gradle_command(batch, batch_num)

        # ✅ Append the full content of 1.txt to the report
        if dep_file.exists() and dep_file.stat().st_size > 0:
            self._write_report("\n--- Full Gradle Dependency Tree ---")
            with open(dep_file, "r", encoding="utf-8") as f:
                self._write_report(f.read().strip())
            self._write_report("\n---------------------------------------------------")

        self._write_report("\n✅ All batches complete.")
        self._write_report(f"📄 Full dependency tree saved at: {dep_file}")
        return True
