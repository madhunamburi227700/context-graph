import subprocess
from pathlib import Path


# ---------------------- Load Only Frameworks ---------------------- #
def load_frameworks_only(frameworks_file: str):
    frameworks = []
    inside_framework_section = False

    with open(frameworks_file, "r") as f:
        for line in f:
            line = line.strip()

            if line == "=== FRAMEWORK ===":
                inside_framework_section = True
                continue

            if line == "=== LIBRARY ===":
                break

            if inside_framework_section and line:
                frameworks.append(line)

    return frameworks


# ---------------------- Main Search Function ---------------------- #
def search_frameworks(repo_path: str, frameworks_file: str, output_file: str = "frame.txt"):
    print("\n======= 🔍 DEBUG: Starting search_frameworks() =======")

    repo = Path(repo_path)
    fw_file = Path(frameworks_file)
    output_path = Path(output_file)

    if not repo.exists():
        print(f"❌ ERROR: Repository folder not found: {repo}")
        return

    if not fw_file.exists():
        print(f"❌ ERROR: Framework list file not found: {fw_file}")
        return

    frameworks = load_frameworks_only(frameworks_file)

    print(f"✅ Loaded {len(frameworks)} frameworks from {fw_file}")

    if not frameworks:
        print("❌ ERROR: No frameworks under === FRAMEWORK === section.")
        return

    results = {}
    used_prefixes = set()   # <-- ensures no duplicate prefix searches

    for idx, fw in enumerate(frameworks, 1):
        print(f"\n---- 🔎 Searching for framework {idx}/{len(frameworks)}: '{fw}' ----")

        try:
            # ---------- 1) Search FULL name first ----------
            full_pattern = f"(import .*{fw}.*|require\\(['\"]{fw}['\"]\\))"
            print(f"   ➤ Full search pattern: {full_pattern}")

            output = subprocess.run(
                ["grep", "-RinE", full_pattern, str(repo)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True
            )

            full_matches = output.stdout.strip()

            if full_matches:
                print(f"   ✅ Full match found for '{fw}'")
                results[fw] = full_matches
                continue  # do NOT check prefix
            else:
                print(f"   ❌ No full match for '{fw}'")

            # ---------- 2) Search prefix ONLY IF full match empty ----------
            if "-" in fw:
                prefix = fw.split("-")[0]

                if prefix in used_prefixes:
                    print(f"   ⚠ Prefix '{prefix}' already searched. Skipping.")
                    continue

                used_prefixes.add(prefix)

                prefix_pattern = f"(import .*(^|/){prefix}.*|require\\(['\"]{prefix}['\"]\\))"
                print(f"   ➤ Prefix search pattern: {prefix_pattern}")

                output = subprocess.run(
                    ["grep", "-RinE", prefix_pattern, str(repo)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True
                )

                prefix_matches = output.stdout.strip()

                if prefix_matches:
                    print(f"   ✅ Prefix match found for '{prefix}'")
                    results[prefix] = prefix_matches
                else:
                    print(f"   ❌ No prefix match for '{prefix}'")

        except Exception as e:
            print(f"❌ ERROR searching for {fw}: {e}")

    # ---------------- Write Results ---------------- #
    print("\n======= 📝 Writing results to frame.txt =======")

    with open(output_path, "w") as f:
        if not results:
            f.write("❌ No frameworks found.\n")
            print("⚠ No results.")
        else:
            for fw, lines in results.items():
                f.write(f"\n=== {fw} ===\n{lines}\n")

    print(f"✅ Search completed! Results saved in {output_file}")
    print("======= 🔍 DEBUG: search_frameworks() finished =======\n")
    