import os
import json
from git_clone import clone_and_checkout
from lanuage_detector import detect_language, detect_dependency_manager

def main():
    # Step 0: Ask for GitHub repo
    repo_with_branch = input(
        "Enter the GitHub repo URL with branch (e.g. https://github.com/user/repo.git@branch): "
    ).strip()

    if not repo_with_branch:
        print("❌ Repo URL required.")
        return

    # Step 1: Clone repo
    repo_path = clone_and_checkout(repo_with_branch)
    print(f"\n➡ Repo cloned at: {repo_path}")

    # Step 2: Get language + metadata
    language_info = detect_language(repo_path)
    detected_language = language_info["detected_language"]

    # Print summary
    print("\n📂 File counts by language:")
    for lang, count in language_info["language_counts"].items():
        print(f"   - {lang}: {count} files")

    print("\n🛠 Special files:")
    for key, value in language_info["special_files"].items():
        print(f"   - {key}: {value}")

    print(f"\n📄 Total files in repository: {language_info['total_files']}")
    print(f"📌 Languages found in project: {', '.join(language_info['languages_found'])}")
    print(f"📌 Detected language: {detected_language}")

    # Step 3: Dependency manager
    manager = detect_dependency_manager(repo_path, detected_language)
    print(f"📌 Detected dependency manager: {manager}")

    # Step 4: Save everything to JSON (ROOT FOLDER)
    output_data = {
        "repo_path": repo_path,
        "language_analysis": language_info,
        "dependency_manager": manager
    }

    # SAVE JSON IN CURRENT WORKING DIRECTORY
    root_path = os.path.dirname(repo_path)
    json_path = os.path.join(root_path, "repo_analysis.json")

    with open(json_path, "w") as f:
        json.dump(output_data, f, indent=4)

    print(f"\n📁 JSON file saved at: {json_path}")


if __name__ == "__main__":
    main()
