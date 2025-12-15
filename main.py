import os
import json
from pathlib import Path
from both_supports.os_detect import os_detect
from both_supports.git_clone import clone_and_checkout
from python_flow.lanuage_detector import detect_language, detect_dependency_manager
from both_supports.cdxgen_sbom_generator import ensure_cdxgen, generate_sbom
from both_supports.retrieve_components import find_sbom_file, search_all_types, TYPES
from linux_flow.linux_commands import run_cmd, count_total_files, language_wise_stats, detect_dependency_manager as detect_dep_manager
from linux_flow.search_framework import search_frameworks
from python_flow.windows_search_framework import load_frameworks_from_output, DependencyManager
from generate_dependency_tree.python.python_files_exsist import process_python
from generate_dependency_tree.gradle.gradle_dependency import generate_gradle_dependency_tree
from generate_dependency_tree.maven.maven_dependency_tree import generate_maven_dependency_tree
from generate_dependency_tree.go_lang.files_exstit import process_go

def main():
    # step 0: which os
    os_type = os_detect()
    print(f"🖥 Detected OS: {os_type}")

    # Step 1: Ask for GitHub repo
    repo_with_branch = input(
        "Enter the GitHub repo URL with branch (e.g. https://github.com/user/repo.git@branch): "
    ).strip()

    if not repo_with_branch:
        print("❌ Repo URL required.")
        return

    # Step 2: Clone repo
    repo_path = clone_and_checkout(repo_with_branch)
    print(f"\n➡ Repo cloned at: {repo_path}")

    # from her to start window's_flow
    if os_type =="windows":
        # Step 1: Detect extensions as languages
        language_info = detect_language(repo_path)
        detected_language = language_info["detected_language"]

        # Print summary
        print("\n📂 File counts by language (extension-based):")
        for lang, count in language_info["language_counts"].items():
            print(f"   - {lang}: {count} files")

        print("\n🛠 Special files:")
        for key, value in language_info["special_files"].items():
            print(f"   - {key}: {value}")

        print(f"\n📄 Total files in repository: {language_info['total_files']}")
        print(f"📌 Languages found in project: {', '.join(language_info['languages_found'])}")
        print(f"📌 Detected language (most common extension): {detected_language}")

        # Detect dependency manager
        manager = detect_dependency_manager(repo_path, detected_language)
        print(f"📌 Detected dependency manager: {manager}")

        # Save everything to JSON (in repo root)
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

        # call the generated function for go_lang
        process_go(repo_path)

        # Call your generated function for gradle
        generate_gradle_dependency_tree(repo_path)

        # Call your generated function for maven
        generate_maven_dependency_tree(repo_path)
        
        # step 3 : generating dependency tree for python
        process_python("python-env", repo_path, 1)

        # Step 2: Generate SBOM only if it does NOT already exist
        sbom_file = Path(repo_path) / "sbom.json"

        if sbom_file.exists():
            print(f"\n🔎 sbom.json already exists at: {sbom_file}")
            print("⏩ Skipping SBOM generation.")
        else:
            print("\n📦 sbom.json not found — generating SBOM...")
            generate_sbom(repo_path=Path(repo_path))

        # step 3 : retrieve components in the sbom.json file
        sbom_path = find_sbom_file("sbom.json", repo_path)
        if sbom_path:
            print(f"Found SBOM file at: {sbom_path}")
            # ✅ Save output.txt INSIDE the repo folder
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_file = os.path.join(current_dir, "output.txt")
            search_all_types(sbom_path, TYPES, output_file)

            # Step 4: Load frameworks and search them in repo
            frameworks = load_frameworks_from_output(output_file)
            if not frameworks:
                print("No frameworks found in output.txt")
            else:
                print(f"\n🔍 Searching {len(frameworks)} frameworks in repo...")
                searcher = DependencyManager(repo_path)
                total_matches = searcher.search_all_frameworks(frameworks, output_file="frame.txt")
                print(f"✅ Framework search completed. Total matches: {total_matches}")
                print("Results saved to frame.txt")
        else:
            print("sbom.json not found in current directory or subfolders.")

    # Linux_flow
    else:
        # step 1 : get the repo details like what language,package manager,total files,language based files
        count_total_files(repo_path)
        language_wise_stats(repo_path)
        detect_dep_manager(repo_path)
        print("\n✅ Analysis Completed.")

        # call the generated function for go_lang
        process_go(repo_path)

        # step 3 : generating dependency tree for python
        process_python("python-env", repo_path, 1)

        # Call your generated function for gradle
        generate_gradle_dependency_tree(repo_path)

        # Call your generated function for maven
        generate_maven_dependency_tree(repo_path)

        # Step 2: Generate SBOM only if it does NOT already exist
        sbom_file = Path(repo_path) / "sbom.json"

        if sbom_file.exists():
            print(f"\n🔎 sbom.json already exists at: {sbom_file}")
            print("⏩ Skipping SBOM generation.")
        else:
            print("\n📦 sbom.json not found — generating SBOM...")
            generate_sbom(repo_path=Path(repo_path)) 
    
        # Step 3: Retrieve components in the sbom.json file
        sbom_path = find_sbom_file("sbom.json", repo_path)
        if sbom_path:
            print(f"Found SBOM file at: {sbom_path}")

            # ✅ Save output.txt INSIDE the repo folder
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_txt = os.path.join(current_dir, "output.txt")  # output from search_all_types
            search_all_types(sbom_path, TYPES, output_txt)

            # Step 4: Search the patterns from output.txt
            frame_txt = os.path.join(current_dir, "frame.txt")    # output for framework search results
            search_frameworks(repo_path=repo_path, frameworks_file=output_txt, output_file=frame_txt)
        else:
            print("sbom.json not found in current directory or subfolders.")

if __name__ == "__main__":
    main()
