import os
import re
from pathlib import Path

# -----------------------------
# Utility to write to report
# -----------------------------
def write_output(text, report_file):
    with open(report_file, "a", encoding="utf-8") as f:
        f.write(text + "\n")

# -----------------------------
# Load frameworks from output.txt
# -----------------------------
def load_frameworks_from_output(file_path="output.txt"):
    frameworks = []
    if not os.path.exists(file_path):
        write_output(f"⚠️ {file_path} not found.", file_path)
        return frameworks

    read_fw = False
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == "=== FRAMEWORK ===":
                read_fw = True
                continue
            if line.startswith("===") and read_fw:
                break
            if read_fw and line:
                frameworks.append(line)
    return frameworks

# -----------------------------
# Dependency Manager / Searcher
# -----------------------------
class DependencyManager:
    def __init__(self, repo_root="."):
        self.repo_root = repo_root

    def search_pattern_in_file(self, pattern, file_path):
        matches = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f):
                    if re.search(pattern, line, flags=re.IGNORECASE):
                        matches.append({
                            "file": file_path,
                            "line_number": idx + 1,
                            "line_content": line.rstrip()
                        })
        except Exception:
            pass
        return matches

    def search_framework(self, fw_name):
        results = []
        full_pattern = rf"(import\s+.*{re.escape(fw_name)}.*|require\(['\"]{re.escape(fw_name)}['\"]\))"
        prefixes = []
        if "-" in fw_name:
            prefixes.append(fw_name.split("-")[0])

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                file_path = os.path.join(root, file)

                # Full match
                results.extend(self.search_pattern_in_file(full_pattern, file_path))

                # Prefix match
                for prefix in prefixes:
                    prefix_pattern = rf"(import\s+.*{re.escape(prefix)}.*|require\(['\"]{re.escape(prefix)}['\"]\))"
                    results.extend(self.search_pattern_in_file(prefix_pattern, file_path))
        return results

    def search_all_frameworks(self, frameworks, output_file="frame.txt"):
        total_matches = 0
        with open(output_file, "w", encoding="utf-8") as f:
            if not frameworks:
                f.write("❌ No frameworks found.\n")
                return 0

            for idx, fw in enumerate(frameworks, 1):
                f.write(f"\n=== Searching framework {idx}/{len(frameworks)}: {fw} ===\n")
                matches = self.search_framework(fw)
                if not matches:
                    f.write("No matches found.\n")
                    continue
                for match in matches:
                    f.write(f"{match['file']}:{match['line_number']}: {match['line_content']}\n")
                    total_matches += 1
        return total_matches

# -----------------------------
# Single python Framework Orchestrator
# -----------------------------
def orchestrate_python_framework_search(repo_path, output_file, report_file):
    write_output("\n-----Section 4: Framework Search (frame.txt)-----", report_file)

    # Load frameworks from SBOM output.txt
    frameworks = load_frameworks_from_output(output_file)
    if not frameworks:
        write_output("❌ No frameworks found in output.txt", report_file)
        return

    write_output(f"🔍 Searching {len(frameworks)} frameworks in repository...", report_file)

    searcher = DependencyManager(repo_path)
    frame_file = Path(output_file).parent / "frame.txt"

    total_matches = searcher.search_all_frameworks(frameworks, output_file=str(frame_file))

    write_output(f"✅ Framework search completed. Total matches: {total_matches}", report_file)

    # Write frame.txt contents to report
    write_output("\n--- Contents of frame.txt ---", report_file)
    with open(frame_file, "r", encoding="utf-8") as f:
        for line in f:
            write_output(line.rstrip(), report_file)

    write_output("\n---------------------------------------------------", report_file)
