import subprocess
import os
import json
from pathlib import Path


class GoDependencyHandler:
    def __init__(self, repo_path: Path, output_root: Path, report_file: Path):
        self.repo_path = Path(repo_path)
        self.output_root = Path(output_root)
        self.report_file = Path(report_file)

    # ---------------- Internal helpers ----------------

    def _run_command(self, cmd, cwd=None):
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(
                f"Command failed: {' '.join(cmd)}\nError: {result.stderr.strip()}"
            )
        return result.stdout.strip()

    def _write_report(self, text: str):
        with open(self.report_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    def _install_deptree(self):
        self._write_report("🔧 Installing deptree tool...")
        go_bin = Path.home() / "go" / "bin"
        os.environ["PATH"] += os.pathsep + str(go_bin)
        self._run_command(["go", "install", "github.com/vc60er/deptree@latest"])
        self._write_report("✅ Deptree installed")

    def _generate_dependency_tree(self, module_path: Path, index: int) -> Path:
        graph_output = self._run_command(["go", "mod", "graph"], cwd=module_path)

        proc = subprocess.Popen(
            ["deptree", "-json"],
            cwd=module_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(input=graph_output)
        if proc.returncode != 0:
            raise Exception(stderr.strip())

        output_file = self.output_root / f"go_deps_{index}.json"
        output_file.write_text(stdout, encoding="utf-8")
        return output_file

    # ---------------- PUBLIC METHOD ----------------
    # 👇 THIS IS THE ONLY METHOD main.py CALLS

    def run(self) -> bool:
        self._write_report("\n-----Section 5: Dependency Tree-----")
        self._write_report("-----Section 5.1: Go Modules-----")

        go_mods = list(self.repo_path.rglob("go.mod"))

        if not go_mods:
            self._write_report(
                "⏭️ No Go modules found — skipping Go dependency tree generation."
            )
            return False

        self._write_report(f"📦 Detected {len(go_mods)} Go module(s)")
        self._install_deptree()

        for idx, go_mod in enumerate(go_mods, start=1):
            module_path = go_mod.parent
            self._write_report(f"\n🚀 Processing Go module #{idx}: {module_path}")

            try:
                json_file = self._generate_dependency_tree(module_path, idx)
                self._write_report(f"--- Contents of {json_file.name} ---")

                if json_file.stat().st_size == 0:
                    self._write_report("⚠️ File is empty!")
                    continue

                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                    pretty_json = json.dumps(data, indent=4)
                    self._write_report(pretty_json)
                except json.JSONDecodeError:
                    self._write_report("⚠️ Invalid JSON — raw content below:")
                    self._write_report(json_file.read_text(encoding="utf-8"))

                self._write_report("-" * 50)

            except Exception as e:
                self._write_report(f"❌ Failed for {module_path}")
                self._write_report(f"Error: {e}")

        return True
