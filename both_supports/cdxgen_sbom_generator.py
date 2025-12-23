import subprocess
from pathlib import Path
import shutil
import os
import platform


# -------------------- Ensure cdxgen is installed --------------------
def ensure_cdxgen():
    """Ensure cdxgen is installed and available in PATH."""
    if shutil.which("cdxgen") or shutil.which("cdxgen.cmd"):
        return

    print("❌ cdxgen not found. Installing globally via npm...")
    subprocess.run(["npm", "install", "-g", "@cyclonedx/cdxgen"], check=True)

    npm_bin = subprocess.check_output(["npm", "bin", "-g"], text=True).strip()
    path_sep = ";" if platform.system() == "Windows" else ":"

    if npm_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{npm_bin}{path_sep}{os.environ.get('PATH', '')}"

    if not (shutil.which("cdxgen") or shutil.which("cdxgen.cmd")):
        raise EnvironmentError(
            "❌ Could not find cdxgen after installation. "
            "Restart terminal or add npm global bin to PATH."
        )


# -------------------- Generate SBOM --------------------
def generate_sbom(repo_path: Path) -> Path:
    """
    Generate SBOM using cdxgen.
    Returns path to sbom.json.
    """
    ensure_cdxgen()

    sbom_file = repo_path / "sbom.json"

    print(f"\n📦 Generating SBOM in: {repo_path}")

    cmd = ["cdxgen", "-r", "--json-pretty", "-o", str(sbom_file)]
    use_shell = platform.system() == "Windows"

    try:
        subprocess.run(cmd, cwd=str(repo_path), check=True, shell=use_shell)
    except FileNotFoundError:
        print("⚠️ cdxgen not found, trying npx...")
        subprocess.run(
            ["npx", "cdxgen", "-r", "--json-pretty", "-o", str(sbom_file)],
            cwd=str(repo_path),
            check=True
        )

    print(f"✅ SBOM generated at: {sbom_file}")
    return sbom_file


# -------------------- SIMPLE ORCHESTRATION --------------------
def run_sbom_flow(repo_path) -> Path:
    """
    One-flow orchestration:
    - If sbom.json exists → skip
    - Else → generate SBOM
    """
    # Ensure repo_path is a Path object
    repo_path = Path(repo_path)

    sbom_file = repo_path / "sbom.json"

    if sbom_file.exists():
        print(f"\n🔎 sbom.json already exists at: {sbom_file}")
        print("⏩ Skipping SBOM generation.")
        return sbom_file

    print("\n📦 sbom.json not found — generating SBOM...")
    return generate_sbom(repo_path)

