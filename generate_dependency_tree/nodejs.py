import os
import json
import re
import subprocess
from pathlib import Path


class NodeDependencyHandler:
    def __init__(self, repo_root: Path, output_root: Path, report_file: Path):
        self.repo_root = Path(repo_root).resolve()
        self.output_root = Path(output_root).resolve()
        self.report_file = Path(report_file)
        self.output_root.mkdir(parents=True, exist_ok=True)

    # ---------------- Report helper ----------------
    def _write_report(self, text: str):
        with open(self.report_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    # ---------------- Command helpers ----------------
    def _run_cmd(self, cmd: str, cwd: Path, output_file: Path | None = None) -> bool:
        print(f"▶ Running: {cmd} (in {cwd})")

        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(result.stderr)
            return False

        if output_file:
            output_file.write_text(result.stdout, encoding="utf-8")

        return True

    def _find_package_json_dirs(self):
        package_dirs = []

        for root, dirs, files in os.walk(self.repo_root):
            if "node_modules" in dirs:
                dirs.remove("node_modules")

            if "package.json" in files:
                package_dirs.append(Path(root))

        return package_dirs

    # ---------------- pnpm TXT → JSON ----------------
    def _parse_pnpm_tree(self, txt_file: Path) -> dict:
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
                    "dependencies": [],
                }

                while stack and stack[-1][0] >= depth:
                    stack.pop()

                stack[-1][1]["dependencies"].append(node)
                stack.append((depth, node))

        return root

    def _save_tree_json(self, tree: dict, output_file: Path):
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(tree, f, indent=2)

        print(f"📄 Dependency tree JSON saved → {output_file}")

    # ---------------- Public entry ----------------
    def run(self) -> bool:
        """
        Detect Node.js projects, generate dependency trees,
        and write results into report_file.
        """
        # Section header
        self._write_report("\n-----Section 5.5: Node.js Projects-----")

        print("\n🔍 Checking for Node.js projects...")
        package_dirs = self._find_package_json_dirs()

        if not package_dirs:
            self._write_report(
                "⏭️ No Node.js projects found — skipping dependency tree generation."
            )
            return False

        print(f"✅ Found {len(package_dirs)} Node.js project(s).")

        output_index = 1

        for pkg_dir in package_dirs:
            print(f"\n📦 Processing Node project: {pkg_dir.relative_to(self.repo_root)}")

            # 1️⃣ Install dependencies
            if not self._run_cmd("pnpm install", cwd=pkg_dir):
                print("⏭️ Skipping dependency tree due to install failure.")
                continue

            # 2️⃣ Generate TXT tree
            txt_file = self.output_root / f"node_dependency_tree_{output_index}.txt"
            if not self._run_cmd(
                "pnpm list --depth Infinity",
                cwd=pkg_dir,
                output_file=txt_file,
            ):
                print("⏭️ Dependency tree generation failed.")
                continue

            # 3️⃣ Convert TXT → JSON
            try:
                tree = self._parse_pnpm_tree(txt_file)
                json_file = self.output_root / f"node_dependency_tree_{output_index}.json"
                self._save_tree_json(tree, json_file)
            except Exception as e:
                print(f"⚠️ Failed to convert dependency tree to JSON: {e}")
                continue

            output_index += 1

        # ---------------- Write JSON contents to report ----------------
        for json_file in sorted(self.output_root.glob("node_dependency_tree_*.json")):
            self._write_report(f"\n--- Contents of {json_file.name} ---")

            if json_file.stat().st_size == 0:
                self._write_report("⚠️ File is empty!")
                continue

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._write_report(json.dumps(data, indent=4))
            except json.JSONDecodeError:
                self._write_report(
                    "⚠️ Could not parse JSON — raw content below:"
                )
                self._write_report(
                    json_file.read_text(encoding="utf-8").strip()
                )

            self._write_report("\n---------------------------------------------------")

        return True
