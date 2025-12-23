import json
import os
from pathlib import Path

TYPES = ["framework", "library", "application"]   # all 3 types

# -----------------------------
# Function to find sbom.json recursively
# -----------------------------
def find_sbom_file(filename="sbom.json", start_dir="."):
    """
    Search for sbom.json in current directory and all subdirectories
    Returns the first found full path or None
    """
    for root, dirs, files in os.walk(start_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None

# -----------------------------
# Function to search and write components by type
# -----------------------------
def search_all_types(sbom_file, types, output_file):
    try:
        with open(sbom_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("Error reading file:", e)
        return

    components = data.get("components", [])

    with open(output_file, "w", encoding="utf-8") as out:
        for t in types:
            out.write(f"=== {t.upper()} ===\n")
            
            # Find all names of this type
            names = [
                comp.get("name", "")
                for comp in components
                if comp.get("type", "").lower() == t.lower()
            ]

            if names:
                for name in names:
                    out.write(name + "\n")
            else:
                out.write("No components found.\n")

            out.write("\n")  # blank line between sections

    print(f"Saved all types to {output_file}")

# -----------------------------
# Write output to report and console
# -----------------------------
def write_output(text, report_file):
    print(text)
    with open(report_file, "a", encoding="utf-8") as f:
        f.write(text + "\n")

# -----------------------------
# Simple Orchestrator
# -----------------------------
def orchestrate_sbom(repo_path, orchestration_root, report_file):
    """
    Simple SBOM orchestration:
    1. Find sbom.json
    2. Extract all components into output.txt
    3. Write output.txt contents to the report
    """
    write_output("\n-----Section 3: SBOM Components (output.txt)-----", report_file)

    repo_path = Path(repo_path).resolve()
    orchestration_root = Path(orchestration_root).resolve()
    orchestration_root.mkdir(parents=True, exist_ok=True)

    sbom_path = find_sbom_file("sbom.json", repo_path)
    if not sbom_path:
        write_output("❌ sbom.json not found in current directory or subfolders.", report_file)
        return

    write_output(f"Found SBOM file at: {sbom_path}", report_file)

    # Generate output.txt from SBOM
    output_file = orchestration_root / "output.txt"
    search_all_types(sbom_path, TYPES, str(output_file))

    # Read output.txt content and write to report
    write_output("\n--- Contents of output.txt ---", report_file)
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            write_output(line.strip(), report_file)

    write_output("\n---------------------------------------------------", report_file)

