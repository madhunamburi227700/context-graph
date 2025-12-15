import os
import re

# ------------------ Helper to load frameworks ------------------ #
def load_frameworks_from_output(file_path="output.txt"):
    print("\n======= 📥 DEBUG: Loading frameworks =======")
    frameworks = []

    if not os.path.exists(file_path):
        print(f"⚠️ DEBUG: {file_path} not found.")
        return frameworks

    read_fw = False
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line == "=== FRAMEWORK ===":
                print("✅ DEBUG: Entered FRAMEWORK section")
                read_fw = True
                continue

            if line.startswith("===") and read_fw:
                print("🛑 DEBUG: Exiting FRAMEWORK section")
                break

            if read_fw and line:
                print(f"➕ DEBUG: Found framework: {line}")
                frameworks.append(line)

    print(f"✅ DEBUG: Total frameworks loaded: {len(frameworks)}")
    print("======= 📥 DEBUG: Framework loading finished =======\n")
    return frameworks


# ------------------ Dependency Manager / Searcher ------------------ #
class DependencyManager:
    def __init__(self, repo_root="."):
        self.repo_root = repo_root
        print(f"📁 DEBUG: Repo root set to: {self.repo_root}")

    def search_pattern_in_file(self, pattern, file_path):
        matches = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f):
                    if re.search(pattern, line, flags=re.IGNORECASE):
                        print(f"   ✅ DEBUG: Match in {file_path}:{idx+1}")
                        matches.append({
                            "file": file_path,
                            "line_number": idx + 1,
                            "line_content": line.rstrip()
                        })
        except Exception as e:
            print(f"⚠️ DEBUG: Failed to read file {file_path} ({e})")
        return matches

    def search_framework(self, fw_name):
        print(f"\n---- 🔍 DEBUG: Searching framework: {fw_name} ----")
        results = []

        # Full framework search
        full_pattern = rf"(import\s+.*{re.escape(fw_name)}.*|require\(['\"]{re.escape(fw_name)}['\"]\))"
        print(f"   ➤ DEBUG: Full search regex: {full_pattern}")

        prefixes = []
        if "-" in fw_name:
            prefix = fw_name.split("-")[0]
            prefixes.append(prefix)
            print(f"   ➤ DEBUG: Prefix extracted: {prefix}")

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                file_path = os.path.join(root, file)

                # Full match search
                full_matches = self.search_pattern_in_file(full_pattern, file_path)
                if full_matches:
                    print(f"   ✅ DEBUG: Full match found for '{fw_name}' in {file_path}")
                    results.extend(full_matches)
                    continue

                # Prefix search
                for prefix in prefixes:
                    prefix_pattern = rf"(import\s+.*{re.escape(prefix)}.*|require\(['\"]{re.escape(prefix)}['\"]\))"
                    print(f"   ➤ DEBUG: Prefix search regex: {prefix_pattern}")

                    prefix_matches = self.search_pattern_in_file(prefix_pattern, file_path)
                    if prefix_matches:
                        print(f"   ✅ DEBUG: Prefix match found for '{prefix}' in {file_path}")
                        results.extend(prefix_matches)

        if not results:
            print(f"   ❌ DEBUG: No matches found for '{fw_name}'")

        return results

    def search_all_frameworks(self, frameworks, output_file="frame.txt"):
        print("\n======= 🔎 DEBUG: Starting framework search =======")
        total_matches = 0

        with open(output_file, "w", encoding="utf-8") as f:
            if not frameworks:
                print("❌ DEBUG: No frameworks provided")
                f.write("❌ No frameworks found.\n")
                return 0

            for idx, fw in enumerate(frameworks, 1):
                print(f"\n---- 🔎 DEBUG: [{idx}/{len(frameworks)}] {fw} ----")
                f.write(f"\n=== Searching framework {idx}/{len(frameworks)}: {fw} ===\n")

                matches = self.search_framework(fw)

                if not matches:
                    print(f"⚠️ DEBUG: No matches for {fw}")
                    f.write("No matches found.\n")
                    continue

                for match in matches:
                    f.write(f"{match['file']}:{match['line_number']}: {match['line_content']}\n")
                    total_matches += 1

        print(f"\n✅ DEBUG: Search completed. Total matches found: {total_matches}")
        print(f"📝 DEBUG: Results written to {output_file}")
        print("======= 🔎 DEBUG: Framework search finished =======\n")
        return total_matches
