import os
import json
from pathlib import Path
import sys

from both_supports.os_detect import run_os_detection
from both_supports.git_clone import clone_and_checkout
from both_supports.cdxgen_sbom_generator import run_sbom_flow
from both_supports.retrieve_components import TYPES, orchestrate_sbom, find_sbom_file

from python_flow.lanuage_detector import LanguageDependencyAnalyzer
from python_flow.windows_search_framework import orchestrate_python_framework_search, DependencyManager, load_frameworks_from_output

from linux_flow.repo_analizer import RepoAnalyzer
from linux_flow.search_framework import orchestrate_linux_framework_search, search_frameworks, load_frameworks_only

from generate_dependency_tree.go import GoDependencyHandler
from generate_dependency_tree.maven import MavenDependencyHandler
from generate_dependency_tree.gradle import GradleDependencyHandler
from generate_dependency_tree.nodejs import NodeDependencyHandler
from generate_dependency_tree.python import PythonDependencyHandler

def main():
    # Ask for analysis folder name FIRST
    run_folder_name = input("Enter analysis folder name :").strip()

    if not run_folder_name:
        print("❌ Folder name is required.")
        return

    base_root = Path(__file__).parent.resolve()
    orchestration_root = base_root / run_folder_name
    orchestration_root.mkdir(parents=True, exist_ok=True)
    print(f"📁 Analysis folder created at: {orchestration_root}")

    # Step 1: Ask for GitHub repo
    repo_with_branch = input("Enter the GitHub repo URL with branch (e.g. https://github.com/user/repo.git@branch): ").strip()

    if not repo_with_branch:
        print("❌ Repo URL required.")
        return

    # Step 2: Clone repo
    repo_path = clone_and_checkout(repo_with_branch,base_dir=orchestration_root)
    repo_name = Path(repo_path).name
    # Create consolidatefile INSIDE orchestration folder
    report_file = orchestration_root / f"{repo_name}_consolidate.txt"
    report_file.write_text("")  # clear old content ONCE


    print(f"\n➡ Repo cloned at: {repo_path}")

    # Step 3: Detect OS type
    os_type = run_os_detection()


# --------------------------------------------------
    # linux flow
# --------------------------------------------------
    if os_type =="windows":

        # step 2: repo analysis in linux
        analyzer = RepoAnalyzer(repo_path=repo_path,report_file=report_file)
        analyzer.run()

        # step 3: sbom generator
        run_sbom_flow(repo_path)

        # ------------------Section 3: SBOM Components----------------------


        sbom_path = find_sbom_file("sbom.json", repo_path)
        if sbom_path:

            orchestrate_sbom(repo_path, orchestration_root, report_file)


            # 3️⃣ Define SBOM output.txt path for framework search
            sbom_output_file = orchestration_root / "output.txt"

            # 4️⃣ Linux framework search
            orchestrate_linux_framework_search(repo_path=repo_path,output_file=sbom_output_file,report_file=report_file)

        else:
            print("sbom.json not found in current directory or subfolders.", report_file)

# --------------------------------------------------
    # python flow
# --------------------------------------------------
    else:

        # Step 2: Language Dependency Analysis for python flow
        analyzer = LanguageDependencyAnalyzer(repo_path=repo_path,report_file=report_file,orchestration_root=orchestration_root)
        analyzer.run()

        # step 3: sbom generator
        run_sbom_flow(repo_path)           

        # ------------------Section 3.1: SBOM Components----------------------
        sbom_path = find_sbom_file("sbom.json", repo_path)

        if sbom_path:

            orchestrate_sbom(repo_path, orchestration_root, report_file)

            # 3️⃣ Define SBOM output.txt path for framework search
            sbom_output_file = orchestration_root / "output.txt"

            # 4️⃣ Run Python framework search
            orchestrate_python_framework_search(repo_path=repo_path,output_file=sbom_output_file,report_file=report_file)

        else:
            print("❌ sbom.json not found in current directory or subfolders.", report_file)

# --------------------------------------------------
    # generate dependency tree
# --------------------------------------------------
    # Call your generated function for Go
    go_handler = GoDependencyHandler(repo_path=repo_path,output_root=orchestration_root,report_file=report_file)
    go_handler.run()

    # call your generated function for Maven
    maven_handler = MavenDependencyHandler(repo_path=repo_path,output_root=orchestration_root,report_file=report_file)
    maven_handler.run()

    # call your generated function for Gradle
    gradle_handler = GradleDependencyHandler(repo_path=repo_path,output_root=orchestration_root,report_file=report_file)
    gradle_handler.run()
    
    # Python dependencies
    python_handler = PythonDependencyHandler(repo_path=repo_path,output_root=orchestration_root,report_file=report_file)
    python_handler.run()

    # call your generated function for nodejs/type_script/javascript
    node_handler = NodeDependencyHandler(repo_root=repo_path,output_root=orchestration_root,report_file=report_file)
    node_handler.run()

if __name__ == "__main__":
    main()
