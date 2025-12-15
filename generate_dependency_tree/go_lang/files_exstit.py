from .dependency_tree import generate_dependency_tree, install_deptree
from pathlib import Path

def process_go(repo_path, output_root):
    """
    Search for all go.mod files in the repo_path,
    generate dependency tree for each module,
    and save outputs in the current working directory.
    """
    repo_root = Path(repo_path)

    # Search recursively for go.mod files
    go_files = list(repo_root.rglob("go.mod"))

    if not go_files:
        print("⚠️ No Go modules found in the repository.")
        return

    print(f"\n📦 Detected {len(go_files)} Go module(s)")

    # Root folder where output files will be saved
    output_root = Path(output_root).resolve()
    install_deptree()  # Install deptree once

    for idx, go_mod in enumerate(go_files, start=1):
        mod_path = Path(go_mod).parent

        print(f"\n🚀 Processing Go module #{idx}: {mod_path}")

        # Step: generate dependency tree
        try:
            deps_file = generate_dependency_tree(
                repo_path=mod_path,
                current_folder=output_root,
                output_name=f"go_deps_{idx}.json"
            )
            print(f"✅ Go dep_tree completed → {deps_file}")

        except Exception as e:
            print(f"❌ Failed generating dependency tree for {mod_path}")
            print(f"   Error: {e}")

            # Save empty JSON to maintain consistent output
            empty_file = output_root / f"go_deps_{idx}.json"
            empty_file.write_text("{}")
            print(f"✅ Empty dependency tree saved → {empty_file}")
