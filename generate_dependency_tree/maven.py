import shutil
import subprocess
import platform
from pathlib import Path
import json
import re

class MavenDependencyHandler:
    DEP_LINE_RE = re.compile(r'^\s*[\|\s\\+]*[\\+]-\s+(.+)$')
    DEP_PREFIX_RE = re.compile(r'^(\s*[\|\s\\+]*?)[\\+]-')

    def __init__(self, repo_path: Path, output_root: Path, report_file: Path):
        self.repo_path = Path(repo_path)
        self.output_root = Path(output_root)
        self.report_file = Path(report_file)

    # ---------------- Internal helpers ----------------
    def _write_report(self, text: str):
        with open(self.report_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    def _get_mvn_path(self) -> Path:
        mvn_bin = "mvn.cmd" if platform.system() == "Windows" else "mvn"
        mvn_path = shutil.which(mvn_bin)

        if not mvn_path:
            raise FileNotFoundError(
                f"❌ Maven not found on PATH. Please install Maven and ensure '{mvn_bin}' is available."
            )

        result = subprocess.run([mvn_path, "-v"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"❌ Maven found at {mvn_path} but failed to run.")

        self._write_report(f"✅ Using system Maven: {mvn_path}")
        return Path(mvn_path)

    def _parse_dependencies(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            self._write_report(f"❌ File '{file_path}' not found.")
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
            m = self.DEP_PREFIX_RE.match(line)
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

            m = self.DEP_LINE_RE.match(raw_line)
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

    def _save_json(self, parsed_data, output_file: Path):
        try:
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2)
            self._write_report(f"✅ Dependencies JSON saved to {output_file}")
        except Exception as e:
            self._write_report(f"❌ Error writing JSON: {e}")

    # ---------------- PUBLIC METHOD ----------------
    def run(self) -> bool:
        self._write_report("\n-----Section 5.2: Maven Projects-----")

        # STEP 1: Detect pom.xml FIRST
        pom_files = list(self.repo_path.rglob("pom.xml"))
        if not pom_files:
            self._write_report("⏭️ No Maven projects found — skipping dependency tree generation.")
            return False

        # STEP 2: Resolve Maven ONLY if needed
        try:
            mvn = self._get_mvn_path()
        except Exception as e:
            self._write_report(str(e))
            self._write_report("⏭️ Skipping Maven dependency tree.")
            return False

        self._write_report(f"🔍 Found {len(pom_files)} pom.xml file(s).")

        # STEP 3: Process each Maven module
        for idx, pom in enumerate(pom_files, start=1):
            module_dir = pom.parent
            self._write_report(f"\n📦 Processing Maven module #{idx}: {module_dir}")

            output_txt = self.output_root / f"dependency_tree_{idx}.txt"
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
                self._write_report(f"❌ Maven failed for {module_dir}")
                self._write_report(result.stderr)
                continue

            self._write_report(f"✅ Maven dependency tree saved → {output_txt}")

            # Parse and save JSON
            try:
                parsed = self._parse_dependencies(output_txt)
                output_json = self.output_root / f"maven_dependency_tree_{idx}.json"
                self._save_json(parsed, output_json)

                # ✅ Append JSON content to report
                if output_json.exists() and output_json.stat().st_size > 0:
                    with open(output_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        pretty_json = json.dumps(data, indent=4)
                        self._write_report(f"\n--- Contents of {output_json.name} ---")
                        self._write_report(pretty_json)
                        self._write_report("\n---------------------------------------------------")

            except Exception as e:
                self._write_report(f"❌ Failed to parse Maven output for {module_dir}: {e}")

        return True
