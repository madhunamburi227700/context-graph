import subprocess
from pathlib import Path
import os

def run_command(cmd, cwd=None):
    """Run a shell command in a specific directory and raise an exception if it fails."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {' '.join(cmd)}\nError: {result.stderr.strip()}")
    return result.stdout.strip()

def prepare_dependencies(repo_path: Path):
    """Run 'go mod tidy' inside the repo."""
    print("Running go mod tidy...")
    run_command(["go", "mod", "tidy"], cwd=repo_path)
    print("✅ Dependencies prepared.")

def install_deptree():
    """Install deptree if not installed."""
    print("Installing deptree from vc60er/deptree...")
    
    # Ensure Go bin is in PATH so subprocess can find deptree
    go_bin = Path.home() / "go" / "bin"
    os.environ["PATH"] += os.pathsep + str(go_bin)

    run_command(["go", "install", "github.com/vc60er/deptree@latest"])
    print("✅ Deptree installed.")

def generate_dependency_tree(repo_path: Path, current_folder: Path, output_name: str = "deps.json"):
    """Generate dependency tree JSON using deptree."""
    print("Generating dependency tree...")

    repo_path = Path(repo_path)
    current_folder = Path(current_folder)
    current_folder.mkdir(parents=True, exist_ok=True)

    # Run go mod graph
    graph_output = run_command(["go", "mod", "graph"], cwd=repo_path)

    # Run deptree with stdin
    deptree_cmd = ["deptree", "-json"]
    proc = subprocess.Popen(
        deptree_cmd,
        cwd=repo_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=graph_output)
    if proc.returncode != 0:
        raise Exception(f"Deptree command failed:\n{stderr.strip()}")

    # Save JSON output
    t_file = current_folder / output_name
    t_file.write_text(stdout, encoding="utf-8")
    print(f"✅ Dependency tree saved to {t_file}")
    return t_file
