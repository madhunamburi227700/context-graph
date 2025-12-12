import subprocess
from pathlib import Path
import shutil
import os
import platform

# -------------------- Ensure cdxgen is installed --------------------
def ensure_cdxgen():
    """Ensure cdxgen is installed and available in PATH."""
    # Check for cdxgen executable
    cdxgen_path = shutil.which("cdxgen") or shutil.which("cdxgen.cmd")
    if cdxgen_path:
        return

    print("❌ cdxgen not found. Installing globally via npm...")
    subprocess.run(["npm", "install", "-g", "@cyclonedx/cdxgen"], check=True)

    # Add npm global bin directory to PATH
    npm_bin = subprocess.check_output(["npm", "bin", "-g"], text=True).strip()
    path_sep = ";" if platform.system() == "Windows" else ":"

    if npm_bin not in os.environ["PATH"]:
        os.environ["PATH"] = f"{npm_bin}{path_sep}{os.environ['PATH']}"

    # Verify installation again
    cdxgen_path = shutil.which("cdxgen") or shutil.which("cdxgen.cmd")
    if not cdxgen_path:
        raise EnvironmentError(
            "❌ Could not find cdxgen after installation. "
            "Try restarting the terminal or add npm global bin to PATH."
        )

# -------------------- Generate SBOM --------------------
def generate_sbom(repo_path: Path):
    """
    Generate SBOM using cdxgen inside the cloned repo.
    Saves output as repo_path/sbom.json.
    Works on both Windows and Linux.
    """
    ensure_cdxgen()

    sbom_file = repo_path / "sbom.json"

    print(f"📦 Generating SBOM using cdxgen in: {repo_path}")
    print(f"📄 SBOM Output File: {sbom_file}")

    # Base command
    cmd = ["cdxgen", "-r", "--json-pretty", "-o", str(sbom_file)]

    # On Linux: shell=False (required)
    # On Windows: shell=True is OPTIONAL but safe
    use_shell = (platform.system() == "Windows")

    try:
        subprocess.run(
            cmd,
            cwd=str(repo_path),
            check=True,
            shell=use_shell
        )
    except FileNotFoundError:
        print("⚠️ cdxgen command not found, trying with npx...")
        subprocess.run(
            ["npx", "cdxgen", "-r", "--json-pretty", "-o", str(sbom_file)],
            cwd=str(repo_path),
            check=True
        )

    print(f"✅ SBOM generated at: {sbom_file}")
