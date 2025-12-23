import subprocess
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO


class RepoAnalyzer:
    def __init__(self, repo_path: str | Path, report_file: str | Path):
        self.repo_path = Path(repo_path).resolve()
        self.report_file = Path(report_file).resolve()

    # ---------------- Helpers ----------------
    def _run_cmd(self, cmd, cwd=None):
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()

    def _write_output(self, text: str):
        with open(self.report_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    def _capture_output(self, func, *args):
        buffer = StringIO()
        with redirect_stdout(buffer):
            func(*args)
        return buffer.getvalue()

    # ---------------- Analysis Steps ----------------
    def count_total_files(self):
        print("\n📄 Counting total files...")
        cmd = "find . -type f | wc -l"
        output = self._run_cmd(cmd, cwd=self.repo_path)
        print(f"➡ Total files: {output}")

    def language_wise_stats(self):
        print("\n📊 Language wise file count...")
        cmd = 'find . -type f -printf "%f\\n" | awk -F. \'{print $NF}\' | sort | uniq -c'
        output = self._run_cmd(cmd, cwd=self.repo_path)
        print(output)

    def detect_dependency_manager(self):
        print("\n🛠 Detecting dependency manager...")
        cmd = r'''
        find . -maxdepth 5 -type f \( \
            -name "package.json" -o \
            -name "pom.xml" -o \
            -name "build.gradle" -o \
            -name "build.gradle.kts" -o \
            -name "go.mod" -o \
            -name "requirements.txt" -o \
            -name "Pipfile" -o \
            -name "Pipfile.lock" -o \
            -name "poetry.lock" -o \
            -name "uv.lock" -o \
            -name "Cargo.toml" -o \
            -name "composer.json" \
        \) 2>/dev/null | awk '
            /package.json/      {print "npm / yarn / pnpm"; exit}
            /pom.xml/           {print "maven"; exit}
            /build.gradle/      {print "gradle"; exit}
            /build.gradle.kts/  {print "gradle"; exit}
            /go.mod/            {print "go modules"; exit}
            /requirements.txt/  {print "pip"; exit}
            /Pipfile.lock/      {print "pipenv"; exit}
            /Pipfile/           {print "pipenv"; exit}
            /poetry.lock/       {print "poetry"; exit}
            /uv.lock/           {print "uv"; exit}
            /Cargo.toml/        {print "cargo"; exit}
            /composer.json/     {print "composer"; exit}
            {print "Unknown"}
        '
        '''
        output = self._run_cmd(cmd, cwd=self.repo_path)
        print(f"➡ Dependency Manager: {output}")

    # ---------------- Main Orchestration ----------------
    def run(self):
        self._write_output("\n-----Section 2: Language & Package Manager (Linux)-----")

        output = self._capture_output(self.count_total_files)
        self._write_output(output.strip())

        output = self._capture_output(self.language_wise_stats)
        self._write_output(output.strip())

        output = self._capture_output(self.detect_dependency_manager)
        self._write_output(output.strip())

        self._write_output("\n✅ Analysis Completed.")
        self._write_output("\n---------------------------------------------------")
