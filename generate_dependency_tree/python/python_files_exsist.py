import os
from pathlib import Path
from .venv_manager import setup, remove_venv
from .deps import install_dependencies
from .convert_deps import convert_json

def process_python(env_name, repo_path, index):
    repo_path = Path(repo_path)

    # ---------------------------------------------
    # 1. Detect ALL Python dependency files
    # ---------------------------------------------
    valid_files = [
        "pyproject.toml",
        "requirements.txt"
    ]

    found_files = [f for f in valid_files if (repo_path / f).exists()]

    if not found_files:
        print("⚠️ No Python dependency files found. Skipping Python processing.")
        return

    print(f"\n===============================================")
    print(f"▶ Found Python dependency files: {found_files}")
    print(f"===============================================\n")

    # ---------------------------------------------
    # 2. Process each file separately
    # ---------------------------------------------
    file_count = 1
    for selected_file in found_files:
        print(f"\n-----------------------------------------------")
        print(f"📦 Processing dependency file: {selected_file}")
        print(f"-----------------------------------------------\n")

        # Filenames for output
        all_dep_file = f"python_all-dep_{index}_{file_count}.txt"
        dets_file = f"python_dets_{index}_{file_count}.json"
        normalized_file = f"python_normalized_{index}_{file_count}.json"

        # 3. Create venv
        venv_path = setup(env_name=f"{env_name}-{file_count}", project_path=repo_path)

        # 4. Install deps + generate tree
        install_dependencies(
            f"{env_name}-{file_count}",
            repo_path,
            selected_file,
            all_dep_file,
            dets_file
        )

        # 5. Normalize JSON
        if os.path.exists(dets_file):
            convert_json(dets_file, normalized_file)

        # 6. Remove venv
        remove_venv(venv_path)

        file_count += 1

    print("\n🎉 Finished processing ALL Python dependency files")
