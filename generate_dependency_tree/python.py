import os
import sys
import json
import shutil
import subprocess
import platform
from pathlib import Path


class PythonDependencyHandler:
    def __init__(self, repo_path: str | Path, output_root: str | Path, report_file: str | Path, env_name="python-env"):
        self.repo_path = Path(repo_path).resolve()
        self.output_root = Path(output_root).resolve()
        self.report_file = Path(report_file).resolve()
        self.env_name = env_name
        self.output_root.mkdir(parents=True, exist_ok=True)

    # ---------------- Report helper ----------------
    def _write_report(self, text: str):
        with open(self.report_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    # ---------------- Virtual Environment ----------------
    def _find_python_executable(self):
        for cmd in ("python3", "python"):
            if shutil.which(cmd):
                return cmd
        return sys.executable

    def _setup_venv(self, env_name, project_path):
        if not project_path:
            project_path = os.getcwd()
        venv_path = os.path.join(project_path, env_name)
        python_cmd = self._find_python_executable()

        # print("\n=== Step 1: Check Python version ===")
        subprocess.run([python_cmd, "--version"], check=True)

        if not os.path.exists(venv_path):
            # print(f"\n=== Step 2: Creating venv '{env_name}' with uv ===")
            subprocess.run(["uv", "venv", venv_path], check=True)
        else:
            print(f"\n✔ Virtual environment already exists at: {venv_path}")

        system = platform.system()
        python_exec = os.path.join(
            venv_path,
            "Scripts" if system == "Windows" else "bin",
            "python.exe" if system == "Windows" else "python"
        )
        # print(f"\n✔ Virtual environment ready. Python executable: {python_exec}")
        return venv_path

    def _remove_venv(self, venv_path):
        if os.path.exists(venv_path):
            # print(f"\n🗑 Removing virtual environment at: {venv_path}")
            shutil.rmtree(venv_path, ignore_errors=True)
            # print("✔ Virtual environment removed successfully.")
        else:
            print(f"\n⚠️ Virtual environment not found at: {venv_path}")

    # ---------------- Dependency Installation ----------------
    def _install_dependencies(self, env_name, repo_path, dep_file, all_dep_output, dets_output):
        repo_path = str(repo_path)
        venv_path = os.path.join(repo_path, env_name)

        system = platform.system()
        bin_dir = "Scripts" if system == "Windows" else "bin"

        python_exec = os.path.join(
            venv_path,
            bin_dir,
            "python.exe" if system == "Windows" else "python"
        )
        pipgrip_exec = os.path.join(
            venv_path,
            bin_dir,
            "pipgrip.exe" if system == "Windows" else "pipgrip"
        )

        # Install pipgrip
        # print("\n🔧 Installing pipgrip inside venv...")
        try:
            subprocess.run(
                ["uv", "pip", "install", "pipgrip", "--python", python_exec],
                check=True
            )
        except subprocess.CalledProcessError:
            subprocess.run([python_exec, "-m", "pip", "install", "pipgrip"], check=True)

        pipgrip_cmd = [pipgrip_exec] if os.path.exists(pipgrip_exec) else [python_exec, "-m", "pipgrip.cli"]

        dep_path = os.path.join(repo_path, str(dep_file))
        if dep_file.endswith("pyproject.toml"):
            # print(f"\n📄 Processing pyproject.toml: {dep_file}")
            subprocess.run(
                ["uv", "pip", "compile", "--all-extras", dep_path, "-o", all_dep_output],
                check=True
            )
        elif dep_file.endswith("requirements.txt"):
            print(f"\n📄 Processing requirements.txt: {dep_file}")
            subprocess.run(
                ["uv", "pip", "compile", dep_path, "-o", all_dep_output],
                check=True
            )
        else:
            print(f"⚠️ Unsupported dependency file: {dep_file}")
            return

        # Generate dets.json
        subprocess.run(
            pipgrip_cmd + ["--tree-json-exact", "-r", all_dep_output],
            stdout=open(dets_output, "w"),
            check=True
        )

        # print(f"✅ all-dep → {all_dep_output}")
        # print(f"✅ dets.json → {dets_output}")

    # ---------------- JSON Conversion ----------------
    def _load_dependencies_from_json(self, file_path):
        if not os.path.exists(file_path):
            print(f"❌ Error: File '{file_path}' not found.")
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in '{file_path}'")
            return {}

    def _convert_json(self, json_input, json_output):
        if not os.path.exists(json_input):
            print(f"⚠️ Input file '{json_input}' not found. Skipping normalization.")
            return {}

        raw = self._load_dependencies_from_json(json_input)

        def normalize(node):
            deps = []
            for key, sub in node.items():
                pkg, ver = key.split("==", 1) if "==" in key else (key, "")
                deps.append({
                    "package_name": pkg,
                    "installed_version": ver,
                    "required_version": "Any",
                    "dependencies": normalize(sub) if isinstance(sub, dict) else []
                })
            return deps

        normalized = normalize(raw)
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump({"dependencies": normalized}, f, indent=2)

        print(f"✅ Normalized dependencies saved to {json_output}")
        return normalized

# Only changes in the `run()` method and _convert_json logic
# Rest of your class remains the same

    # ---------------- Main orchestration ----------------
    def run(self) -> bool:
        self._write_report("\n-----Section 5.4: Python Projects-----")

        # print("\n🔍 Checking for Python dependency files...")
        valid_files = {"pyproject.toml", "requirements.txt"}
        found_files = sorted([p.relative_to(self.repo_path) for p in self.repo_path.rglob("*") if p.name in valid_files], key=str)

        if not found_files:
            print("⏭️ No Python dependency files found — skipping Python analysis.")
            self._write_report("⏭️ No Python dependency files found — skipping Python dependency tree generation.")
            return False

        print("✅ Found Python dependency files:")
        for f in found_files:
            print(f"   - {f}")

        combined_output = {"python_dependencies": []}
        file_count = 1

        for selected_file in found_files:
            print(f"\n📦 Processing Python dependency file: {selected_file}")
            project_dir = (self.repo_path / selected_file).parent
            all_dep_file = self.output_root / f"python_all-dep_{file_count}.txt"
            dets_file = self.output_root / f"python_dets_{file_count}.json"
            temp_normalized = self.output_root / f"python_normalization_{file_count}.json"

            try:
                venv_name = f"{self.env_name}-{file_count}"
                venv_path = self._setup_venv(env_name=venv_name, project_path=project_dir)

                self._install_dependencies(venv_name, project_dir, selected_file.name, all_dep_file, dets_file)

                if dets_file.exists():
                    # Always generate the normalization file
                    self._convert_json(dets_file, temp_normalized)
                    with open(temp_normalized, "r", encoding="utf-8") as f:
                        normalized_data = json.load(f)

                    combined_output["python_dependencies"].append({
                        "source_file": str(selected_file),
                        "project_path": str(project_dir.relative_to(self.repo_path)),
                        "data": normalized_data
                    })

                    print(f"✅ Normalization file generated → {temp_normalized}")
                    # Do NOT delete temp_normalized; keep it for inspection

                else:
                    print(f"⚠️ No dependency JSON for {selected_file}")

            except Exception as e:
                print(f"❌ Failed processing {selected_file}: {e}")

            finally:
                if 'venv_path' in locals():
                    self._remove_venv(venv_path)

            file_count += 1

        final_output_file = self.output_root / "python_dependencies_combined.json"
        with open(final_output_file, "w", encoding="utf-8") as f:
            json.dump(combined_output, f, indent=2)

        print(f"\n📄 Combined Python dependencies saved → {final_output_file}")

        # Append to report
        if final_output_file.exists() and final_output_file.stat().st_size > 0:
            self._write_report(f"\n--- Contents of {final_output_file.name} ---")
            with open(final_output_file, "r", encoding="utf-8") as f:
                self._write_report(json.dumps(json.load(f), indent=4))
            self._write_report("\n---------------------------------------------------")
        else:
            self._write_report(f"⚠️ {final_output_file.name} is empty — no dependencies captured.")

        print("🎉 Finished processing Python dependency files.")
        return True
