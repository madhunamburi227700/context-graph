import os
import subprocess
import platform


def install_dependencies(env_name, repo_path, dep_file, all_dep_output, dets_output):
    """
    Install dependencies and generate:
       - python_all-dep_#.txt
       - python_dets_#.json
    """

    repo_path = str(repo_path)
    venv_path = os.path.join(repo_path, env_name)

    system = platform.system()
    bin_dir = "Scripts" if system == "Windows" else "bin"

    python_exec = os.path.join(
        venv_path,
        bin_dir,
        "python.exe" if system == "Windows" else "python"
    )
    pipgrip_exec = os.path.join(
        venv_path,
        bin_dir,
        "pipgrip.exe" if system == "Windows" else "pipgrip"
    )

    # 1. Install pipgrip inside venv
    print("\n🔧 Installing pipgrip inside venv...")
    try:
        subprocess.run(
            ["uv", "pip", "install", "pipgrip", "--python", python_exec],
            check=True
        )
    except subprocess.CalledProcessError:
        subprocess.run([python_exec, "-m", "pip", "install", "pipgrip"], check=True)

    pipgrip_cmd = [pipgrip_exec] if os.path.exists(pipgrip_exec) else [python_exec, "-m", "pipgrip.cli"]

    # 2. Build full dependency file
    dep_path = os.path.join(repo_path, str(dep_file))

    if dep_file.endswith("pyproject.toml"):
        print(f"\n📄 Processing pyproject.toml: {dep_file}")
        subprocess.run(
            ["uv", "pip", "compile", "--all-extras", dep_path, "-o", all_dep_output],
            check=True
        )

    elif dep_file.endswith("requirements.txt"):
        print(f"\n📄 Processing requirements.txt: {dep_file}")
        subprocess.run(
            ["uv", "pip", "compile", dep_path, "-o", all_dep_output],
            check=True
        )

    else:
        print(f"⚠️ Unsupported dependency file: {dep_file}")
        return

    # 3. Generate dets.json
    subprocess.run(
        pipgrip_cmd + ["--tree-json-exact", "-r", all_dep_output],
        stdout=open(dets_output, "w"),
        check=True
    )

    print(f"✅ all-dep → {all_dep_output}")
    print(f"✅ dets.json → {dets_output}")
