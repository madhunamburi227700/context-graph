import json
import os

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

