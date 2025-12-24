import subprocess
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

# -----------------------------
# Search frameworks in repo
# -----------------------------
def search_frameworks(repo_path: str, frameworks_file: str, output_file: str):
    repo = Path(repo_path)
    fw_file = Path(frameworks_file)
    output_path = Path(output_file)
    results = {}
    used_prefixes = set()

    frameworks = load_frameworks_only(frameworks_file)
    write_output(f"🔍 Loaded {len(frameworks)} frameworks from {fw_file}", output_file)

    for idx, fw in enumerate(frameworks, 1):
        write_output(f"\n---- Searching {idx}/{len(frameworks)}: '{fw}' ----", output_file)
        try:
            # Full name search
            full_pattern = f"(import .*{fw}.*|require\\(['\"]{fw}['\"]\\))"
            output = subprocess.run(
                ["grep", "-RinE", full_pattern, str(repo)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True
            )
            full_matches = output.stdout.strip()
            if full_matches:
                results[fw] = full_matches
                continue

            # Prefix search if no full match
            if "-" in fw:
                prefix = fw.split("-")[0]
                if prefix in used_prefixes:
                    continue
                used_prefixes.add(prefix)
                prefix_pattern = f"(import .*(^|/){prefix}.*|require\\(['\"]{prefix}['\"]\\))"
                output = subprocess.run(
                    ["grep", "-RinE", prefix_pattern, str(repo)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True
                )
                prefix_matches = output.stdout.strip()
                if prefix_matches:
                    results[prefix] = prefix_matches
        except Exception as e:
            write_output(f"❌ ERROR searching for {fw}: {e}", output_file)

    # Write results to frame.txt
    with open(output_path, "w") as f:
        if not results:
            f.write("❌ No frameworks found.\n")
        else:
            for fw, lines in results.items():
                f.write(f"\n=== {fw} ===\n{lines}\n")

    write_output(f"✅ Search completed! Results saved in {output_file}", output_file)

# -----------------------------
# Single Orchestrator Call
# -----------------------------
def orchestrate_linux_framework_search(repo_path, output_file, report_file):
    write_output("\n-----Section 4: Framework Search (frame.txt)-----", report_file)
    search_frameworks(repo_path=repo_path, frameworks_file=output_file, output_file=str(Path(output_file).parent / "frame.txt"))

    frame_txt = Path(output_file).parent / "frame.txt"
    write_output("\n--- Contents of frame.txt ---", report_file)
    with open(frame_txt, "r", encoding="utf-8") as f:
        for line in f:
            write_output(line.strip(), report_file)
    write_output("\n---------------------------------------------------", report_file)

