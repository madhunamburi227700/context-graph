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
from generate_dependency_tree.package_json.nodejs import generate_dependency_trees
from generate_dependency_tree.package_json.nodejs_json_format import parse_pnpm_tree
import sys
from io import StringIO
import json

def capture_output(func, *args, **kwargs):
    """Capture printed output of a function as a string."""
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    try:
        func(*args, **kwargs)
    finally:
        sys.stdout = old_stdout
    return mystdout.getvalue()

def write_output(text: str, file_path: Path):
    """Print and append text to a file."""
    print(text)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def main():
    # Ask for analysis folder name FIRST
    run_folder_name = input("Enter analysis folder name (e.g. spinnaker_analysis): ").strip()

    if not run_folder_name:
        print("❌ Folder name is required.")
        return

    base_root = Path(__file__).parent.resolve()

    orchestration_root = base_root / run_folder_name
    orchestration_root.mkdir(parents=True, exist_ok=True)

    print(f"📁 Analysis folder created at: {orchestration_root}")

    # Create report.txt INSIDE orchestration folder
    report_file = orchestration_root / "report.txt"
    report_file.write_text("")  # clear old content ONCE

    # Step 1: Ask for GitHub repo
    repo_with_branch = input(
        "Enter the GitHub repo URL with branch (e.g. https://github.com/user/repo.git@branch): "
    ).strip()

    if not repo_with_branch:
        print("❌ Repo URL required.")
        return

    # Step 2: Clone repo
    repo_path = clone_and_checkout(repo_with_branch,base_dir=orchestration_root)

    print(f"\n➡ Repo cloned at: {repo_path}")

    # step 0: which os
    os_type = os_detect()
    print(f"🖥 Detected OS: {os_type}")

    # ------------------1st section----------------------
    write_output("------------------1st section----------------------", report_file)

    # Step 0: Detect OS
    os_type = os_detect()
    write_output(f"🖥 Detected OS: {os_type}", report_file)

    write_output("\n---------------------------------------------------", report_file)

    # ------------------Section 2: Language & Package Manager (Linux)----------------------
    write_output("\n-----Section 2: Language & Package Manager (Linux)-----", report_file)


# windows flow
    if os_type =="windows":
        # Step 1: Detect extensions as languages
        # ------------------Section 2.1: Language & Dependency Manager (Windows)----------------------
        write_output("\n-----Section 2.1: Language & Dependency Manager (Windows)-----", report_file)

        language_info = detect_language(repo_path)
        detected_language = language_info["detected_language"]

        write_output("\n📂 File counts by language (extension-based):", report_file)
        for lang, count in language_info["language_counts"].items():
            write_output(f"   - {lang}: {count} files", report_file)

        write_output("\n🛠 Special files:", report_file)
        for key, value in language_info["special_files"].items():
            write_output(f"   - {key}: {value}", report_file)

        write_output(f"\n📄 Total files in repository: {language_info['total_files']}", report_file)
        write_output(
            f"📌 Languages found in project: {', '.join(language_info['languages_found'])}",
            report_file
        )
        write_output(
            f"📌 Detected language (most common extension): {detected_language}",
            report_file
        )

        # Detect dependency manager
        manager = detect_dependency_manager(repo_path, detected_language)
        write_output(f"📌 Detected dependency manager: {manager}", report_file)
        
        output_data = {
            "repo_path": str(repo_path),
            "language_analysis": language_info,
            "dependency_manager": manager
        }

        json_path = orchestration_root / "repo_analysis.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4)

        write_output(f"\n📁 Windows analysis JSON saved at: {json_path}", report_file)
        write_output("\n---------------------------------------------------", report_file)

        # ------------------Section 3: SBOM Generation (Windows)----------------------
        write_output("\n-----Section 3: SBOM Generation (Windows)-----", report_file)

        sbom_file = Path(repo_path) / "sbom.json"

        if sbom_file.exists():
            write_output(f"\n🔎 sbom.json already exists at: {sbom_file}", report_file)
            write_output("⏩ Skipping SBOM generation.", report_file)
        else:
            write_output("\n📦 sbom.json not found — generating SBOM...", report_file)
            generate_sbom(repo_path=Path(repo_path))


        # ------------------Section 3.1: SBOM Components----------------------
        write_output("\n-----Section 3.1: SBOM Components (output.txt)-----", report_file)

        sbom_path = find_sbom_file("sbom.json", repo_path)

        if sbom_path:
            write_output(f"Found SBOM file at: {sbom_path}", report_file)

            output_dir = orchestration_root
            output_dir.mkdir(exist_ok=True)

            output_file = output_dir / "output.txt"
            search_all_types(sbom_path, TYPES, str(output_file))

            # Write output.txt into report
            write_output("\n--- Contents of output.txt ---", report_file)
            with open(output_file, "r", encoding="utf-8") as f:
                for line in f:
                    write_output(line.rstrip(), report_file)

            write_output("\n---------------------------------------------------", report_file)

            # ------------------Section 4: Framework Search----------------------
            write_output("\n-----Section 4: Framework Search (frame.txt)-----", report_file)

            frameworks = load_frameworks_from_output(output_file)

            if not frameworks:
                write_output("❌ No frameworks found in output.txt", report_file)
            else:
                write_output(
                    f"🔍 Searching {len(frameworks)} frameworks in repository...",
                    report_file
                )

                searcher = DependencyManager(repo_path)
                frame_file = output_dir / "frame.txt"

                total_matches = searcher.search_all_frameworks(
                    frameworks,
                    output_file=str(frame_file)
                )

                write_output(
                    f"✅ Framework search completed. Total matches: {total_matches}",
                    report_file
                )

                # Write frame.txt into report
                write_output("\n--- Contents of frame.txt ---", report_file)
                with open(frame_file, "r", encoding="utf-8") as f:
                    for line in f:
                        write_output(line.rstrip(), report_file)

            write_output("\n---------------------------------------------------", report_file)

        else:
            write_output("❌ sbom.json not found in current directory or subfolders.", report_file)


        # generate dependency tree

        # Section header
        write_output("\n-----Section 5: Dependency Tree-----", report_file)
        write_output("-----Section 5.1: Go Modules-----", report_file)

        go_present = process_go(repo_path=repo_path, output_root=orchestration_root)

        if not go_present:
            write_output("⏭️ No Go modules found — skipping Go dependency tree generation.", report_file)
        else:
            # Sort JSON files to keep module order consistent
            for json_file in sorted(orchestration_root.glob("go_deps_*.json")):
                write_output(f"\n--- Contents of {json_file.name} ---", report_file)
                
                if json_file.stat().st_size == 0:
                    write_output("⚠️ File is empty!", report_file)
                    continue

                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        pretty_json = json.dumps(data, indent=4)
                        write_output(pretty_json, report_file)
                except json.JSONDecodeError:
                    write_output("⚠️ Could not parse JSON — raw content below:", report_file)
                    with open(json_file, "r", encoding="utf-8") as f:
                        raw_content = f.read()
                        write_output(raw_content.strip(), report_file)

                write_output("\n---------------------------------------------------", report_file)


        # Call your generated function for gradle
        # Section header
        write_output("\n-----Section 5.2: Gradle Projects-----", report_file)

        gradle_present = generate_gradle_dependency_tree(repo_path=repo_path, output_root=orchestration_root)

        if not gradle_present:
            write_output("⏭️ No Gradle projects found — skipping Gradle dependency tree generation.", report_file)
        else:
            # Append Gradle dependency output to report.txt
            gradle_output_file = orchestration_root / "1.txt"  # ALL_DEP_TREE

            if gradle_output_file.exists() and gradle_output_file.stat().st_size > 0:
                write_output(f"\n--- Contents of {gradle_output_file.name} ---", report_file)
                with open(gradle_output_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    write_output(content.strip(), report_file)
                write_output("\n---------------------------------------------------", report_file)
            else:
                write_output(f"⚠️ {gradle_output_file.name} is empty — no dependencies captured.", report_file)


        # Call your generated function for maven
        # Section header
        write_output("\n-----Section 5.3: Maven Projects-----", report_file)

        maven_present = generate_maven_dependency_tree(repo_path=repo_path, output_root=orchestration_root)

        if not maven_present:
            write_output("⏭️ No Maven projects found — skipping dependency tree generation.", report_file)
        else:
            # Iterate over generated JSON files
            for json_file in sorted(orchestration_root.glob("maven_dependency_tree_*.json")):
                write_output(f"\n--- Contents of {json_file.name} ---", report_file)

                # Check if file is empty
                if json_file.stat().st_size == 0:
                    write_output("⚠️ File is empty!", report_file)
                    continue

                # Try to load and pretty-print JSON
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        pretty_json = json.dumps(data, indent=4)
                        write_output(pretty_json, report_file)
                except json.JSONDecodeError:
                    write_output("⚠️ Could not parse JSON — raw content below:", report_file)
                    with open(json_file, "r", encoding="utf-8") as f:
                        raw_content = f.read()
                        write_output(raw_content.strip(), report_file)

                write_output("\n---------------------------------------------------", report_file)

        
        # step 3 : generating dependency tree for python
        # Section header
        write_output("\n-----Section 5.4: Python Projects-----", report_file)

        python_present = process_python(
            env_name="python-env",
            repo_path=repo_path,
            output_root=orchestration_root,
            index=1
        )

        if not python_present:
            write_output("⏭️ No Python dependency files found — skipping Python dependency tree generation.", report_file)
        else:
            # Append combined JSON dependencies to report.txt
            python_json_file = orchestration_root / "python_dependencies_combined.json"

            if python_json_file.exists() and python_json_file.stat().st_size > 0:
                write_output(f"\n--- Contents of {python_json_file.name} ---", report_file)
                with open(python_json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pretty_json = json.dumps(data, indent=4)
                    write_output(pretty_json, report_file)
                write_output("\n---------------------------------------------------", report_file)
            else:
                write_output(f"⚠️ {python_json_file.name} is empty — no dependencies captured.", report_file)


        # this id package.json detection and generate the dependency tree
        # Section header
        write_output("\n-----Section 5.5: Node.js Projects-----", report_file)

        node_present = generate_dependency_trees(repo_root=repo_path, output_root=orchestration_root)

        if not node_present:
            write_output("⏭️ No Node.js projects found — skipping dependency tree generation.", report_file)
        else:
            # Iterate over generated JSON files
            for json_file in sorted(orchestration_root.glob("node_dependency_tree_*.json")):
                write_output(f"\n--- Contents of {json_file.name} ---", report_file)

                # Check if file is empty
                if json_file.stat().st_size == 0:
                    write_output("⚠️ File is empty!", report_file)
                    continue

                # Try to load and pretty-print JSON
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        pretty_json = json.dumps(data, indent=4)
                        write_output(pretty_json, report_file)
                except json.JSONDecodeError:
                    write_output("⚠️ Could not parse JSON — raw content below:", report_file)
                    with open(json_file, "r", encoding="utf-8") as f:
                        raw_content = f.read()
                        write_output(raw_content.strip(), report_file)

                write_output("\n---------------------------------------------------", report_file)

# linux flow
    else:
        # Step 1: Get repo details and capture output
        output = capture_output(count_total_files, repo_path)
        write_output(output.strip(), report_file)

        output = capture_output(language_wise_stats, repo_path)
        write_output(output.strip(), report_file)

        output = capture_output(detect_dep_manager, repo_path)
        write_output(output.strip(), report_file)

        write_output("\n✅ Analysis Completed.", report_file)

        write_output("\n---------------------------------------------------", report_file)

        # Step 2: Generate SBOM only if it does NOT already exist
        sbom_file = Path(repo_path) / "sbom.json"

        if sbom_file.exists():
            print(f"\n🔎 sbom.json already exists at: {sbom_file}")
            print("⏩ Skipping SBOM generation.")
        else:
            print("\n📦 sbom.json not found — generating SBOM...")
            generate_sbom(repo_path=Path(repo_path)) 

        # ------------------Section 3: SBOM Components----------------------
        write_output("\n-----Section 3: SBOM Components (output.txt)-----", report_file)

        sbom_path = find_sbom_file("sbom.json", repo_path)
        if sbom_path:
            write_output(f"Found SBOM file at: {sbom_path}", report_file)

            # Ensure output directory exists
            output_dir = orchestration_root
            output_dir.mkdir(exist_ok=True)

            # Generate output.txt from SBOM
            output_file = output_dir / "output.txt"
            search_all_types(sbom_path, TYPES, str(output_file))

            # Read output.txt content and write to report
            write_output("\n--- Contents of output.txt ---", report_file)
            with open(output_file, "r", encoding="utf-8") as f:
                for line in f:
                    write_output(line.strip(), report_file)

            write_output("\n---------------------------------------------------", report_file)

            # ------------------Section 4: Framework Search----------------------
            write_output("\n-----Section 4: Framework Search (frame.txt)-----", report_file)

            frame_txt = output_dir / "frame.txt"
            search_frameworks(repo_path=repo_path, frameworks_file=str(output_file), output_file=str(frame_txt))

            # Read frame.txt content and write to report
            write_output("\n--- Contents of frame.txt ---", report_file)
            with open(frame_txt, "r", encoding="utf-8") as f:
                for line in f:
                    write_output(line.strip(), report_file)
            write_output("\n---------------------------------------------------", report_file)

        else:
            write_output("sbom.json not found in current directory or subfolders.", report_file)


        # generate dependency tree

    # Section header
        write_output("\n-----Section 5: Dependency Tree-----", report_file)
        write_output("-----Section 5.1: Go Modules-----", report_file)

        go_present = process_go(repo_path=repo_path, output_root=orchestration_root)

        if not go_present:
            write_output("⏭️ No Go modules found — skipping Go dependency tree generation.", report_file)
        else:
            # Sort JSON files to keep module order consistent
            for json_file in sorted(orchestration_root.glob("go_deps_*.json")):
                write_output(f"\n--- Contents of {json_file.name} ---", report_file)
                
                if json_file.stat().st_size == 0:
                    write_output("⚠️ File is empty!", report_file)
                    continue

                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        pretty_json = json.dumps(data, indent=4)
                        write_output(pretty_json, report_file)
                except json.JSONDecodeError:
                    write_output("⚠️ Could not parse JSON — raw content below:", report_file)
                    with open(json_file, "r", encoding="utf-8") as f:
                        raw_content = f.read()
                        write_output(raw_content.strip(), report_file)

                write_output("\n---------------------------------------------------", report_file)


        # Call your generated function for gradle
        # Section header
        write_output("\n-----Section 5.2: Gradle Projects-----", report_file)

        gradle_present = generate_gradle_dependency_tree(repo_path=repo_path, output_root=orchestration_root)

        if not gradle_present:
            write_output("⏭️ No Gradle projects found — skipping Gradle dependency tree generation.", report_file)
        else:
            # Append Gradle dependency output to report.txt
            gradle_output_file = orchestration_root / "1.txt"  # ALL_DEP_TREE

            if gradle_output_file.exists() and gradle_output_file.stat().st_size > 0:
                write_output(f"\n--- Contents of {gradle_output_file.name} ---", report_file)
                with open(gradle_output_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    write_output(content.strip(), report_file)
                write_output("\n---------------------------------------------------", report_file)
            else:
                write_output(f"⚠️ {gradle_output_file.name} is empty — no dependencies captured.", report_file)


        # Call your generated function for maven
        # Section header
        write_output("\n-----Section 5.3: Maven Projects-----", report_file)

        maven_present = generate_maven_dependency_tree(repo_path=repo_path, output_root=orchestration_root)

        if not maven_present:
            write_output("⏭️ No Maven projects found — skipping dependency tree generation.", report_file)
        else:
            # Iterate over generated JSON files
            for json_file in sorted(orchestration_root.glob("maven_dependency_tree_*.json")):
                write_output(f"\n--- Contents of {json_file.name} ---", report_file)

                # Check if file is empty
                if json_file.stat().st_size == 0:
                    write_output("⚠️ File is empty!", report_file)
                    continue

                # Try to load and pretty-print JSON
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        pretty_json = json.dumps(data, indent=4)
                        write_output(pretty_json, report_file)
                except json.JSONDecodeError:
                    write_output("⚠️ Could not parse JSON — raw content below:", report_file)
                    with open(json_file, "r", encoding="utf-8") as f:
                        raw_content = f.read()
                        write_output(raw_content.strip(), report_file)

                write_output("\n---------------------------------------------------", report_file)

        
        # step 3 : generating dependency tree for python
        # Section header
        write_output("\n-----Section 5.4: Python Projects-----", report_file)

        python_present = process_python(
            env_name="python-env",
            repo_path=repo_path,
            output_root=orchestration_root,
            index=1
        )

        if not python_present:
            write_output("⏭️ No Python dependency files found — skipping Python dependency tree generation.", report_file)
        else:
            # Append combined JSON dependencies to report.txt
            python_json_file = orchestration_root / "python_dependencies_combined.json"

            if python_json_file.exists() and python_json_file.stat().st_size > 0:
                write_output(f"\n--- Contents of {python_json_file.name} ---", report_file)
                with open(python_json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pretty_json = json.dumps(data, indent=4)
                    write_output(pretty_json, report_file)
                write_output("\n---------------------------------------------------", report_file)
            else:
                write_output(f"⚠️ {python_json_file.name} is empty — no dependencies captured.", report_file)


        # this id package.json detection and generate the dependency tree
        # Section header
        write_output("\n-----Section 5.5: Node.js Projects-----", report_file)

        node_present = generate_dependency_trees(repo_root=repo_path, output_root=orchestration_root)

        if not node_present:
            write_output("⏭️ No Node.js projects found — skipping dependency tree generation.", report_file)
        else:
            # Iterate over generated JSON files
            for json_file in sorted(orchestration_root.glob("node_dependency_tree_*.json")):
                write_output(f"\n--- Contents of {json_file.name} ---", report_file)

                # Check if file is empty
                if json_file.stat().st_size == 0:
                    write_output("⚠️ File is empty!", report_file)
                    continue

                # Try to load and pretty-print JSON
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        pretty_json = json.dumps(data, indent=4)
                        write_output(pretty_json, report_file)
                except json.JSONDecodeError:
                    write_output("⚠️ Could not parse JSON — raw content below:", report_file)
                    with open(json_file, "r", encoding="utf-8") as f:
                        raw_content = f.read()
                        write_output(raw_content.strip(), report_file)

                write_output("\n---------------------------------------------------", report_file)


if __name__ == "__main__":
    main()
