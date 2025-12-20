import os
import json
from pathlib import Path
from .venv_manager import setup, remove_venv
from .deps import install_dependencies
from .convert_deps import convert_json


def process_python(env_name, repo_path, output_root, index):
    repo_path = Path(repo_path).resolve()
    output_root = Path(output_root).resolve()

    print("\n🔍 Checking for Python dependency files...")

    valid_files = {"pyproject.toml", "requirements.txt"}

    found_files = sorted(
        [
            p.relative_to(repo_path)
            for p in repo_path.rglob("*")
            if p.name in valid_files
        ],
        key=str
    )

    if not found_files:
        print("⏭️ No Python dependency files found — skipping Python analysis.")
        return False

    print("✅ Found Python dependency files:")
    for f in found_files:
        print(f"   - {f}")

    combined_output = {
        "python_dependencies": []
    }

    file_count = 1

    for selected_file in found_files:
        print(f"\n📦 Processing Python dependency file: {selected_file}")

        project_dir = (repo_path / selected_file).parent

        all_dep_file = output_root / f"python_all-dep_{index}_{file_count}.txt"
        dets_file = output_root / f"python_dets_{index}_{file_count}.json"
        temp_normalized = output_root / f"_tmp_python_norm_{file_count}.json"

        try:
            venv_name = f"{env_name}-{file_count}"
            venv_path = setup(env_name=venv_name, project_path=project_dir)

            install_dependencies(
                venv_name,
                project_dir,
                selected_file.name,
                all_dep_file,
                dets_file
            )

            if dets_file.exists():
                convert_json(dets_file, temp_normalized)

                with open(temp_normalized, "r", encoding="utf-8") as f:
                    normalized_data = json.load(f)

                combined_output["python_dependencies"].append({
                    "source_file": str(selected_file),
                    "project_path": str(project_dir.relative_to(repo_path)),
                    "data": normalized_data
                })

                temp_normalized.unlink(missing_ok=True)
            else:
                print(f"⚠️ No dependency JSON for {selected_file}")

        except Exception as e:
            print(f"❌ Failed processing {selected_file}: {e}")

        finally:
            if 'venv_path' in locals():
                remove_venv(venv_path)

        file_count += 1

    final_output_file = output_root / "python_dependencies_combined.json"
    with open(final_output_file, "w", encoding="utf-8") as f:
        json.dump(combined_output, f, indent=2)

    print(f"\n📄 Combined Python dependencies saved → {final_output_file}")
    print("🎉 Finished processing Python dependency files.")

    return True
