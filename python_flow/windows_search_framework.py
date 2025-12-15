import os
import re

# ------------------ Helper to load frameworks ------------------ #
def load_frameworks_from_output(file_path="output.txt"):
    """
    Reads output.txt and extracts frameworks (between === FRAMEWORK === and === LIBRARY ===)
    """
    frameworks = []
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found.")
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


# ------------------ Dependency Manager / Searcher ------------------ #
class DependencyManager:
    def __init__(self, repo_root="."):
        self.repo_root = repo_root

    def search_pattern_in_file(self, pattern, file_path):
        """
        Search a regex pattern in a single file and return matches as list of dicts
        """
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
        """
        Search framework import/require patterns recursively in repo
        """
        results = []

        # Pattern for full framework name
        full_pattern = rf"(import\s+.*{re.escape(fw_name)}.*|require\(['\"]{re.escape(fw_name)}['\"]\))"

        # If framework has a dash, also search by prefix
        prefixes = []
        if "-" in fw_name:
            prefix = fw_name.split("-")[0]
            prefixes.append(prefix)

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                file_path = os.path.join(root, file)

                # Check full pattern first
                full_matches = self.search_pattern_in_file(full_pattern, file_path)
                if full_matches:
                    results.extend(full_matches)
                    continue  # skip prefix if full match found

                # Check prefixes if any
                for prefix in prefixes:
                    prefix_pattern = rf"(import\s+.*{re.escape(prefix)}.*|require\(['\"]{re.escape(prefix)}['\"]\))"
                    prefix_matches = self.search_pattern_in_file(prefix_pattern, file_path)
                    if prefix_matches:
                        results.extend(prefix_matches)

        return results

    def search_all_frameworks(self, frameworks, output_file="frame.txt"):
        total_matches = 0
        used_prefixes = set()

        with open(output_file, "w", encoding="utf-8") as f:
            if not frameworks:
                f.write("❌ No frameworks found.\n")
                return 0

            for idx, fw in enumerate(frameworks, 1):
                f.write(f"\n=== Searching framework {idx}/{len(frameworks)}: {fw} ===\n")
                matches = self.search_framework(fw)

                # Write matches
                if not matches:
                    f.write("No matches found.\n")
                    continue

                for match in matches:
                    f.write(f"{match['file']}:{match['line_number']}: {match['line_content']}\n")
                    total_matches += 1

        return total_matches

