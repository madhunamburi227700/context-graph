import subprocess
from pathlib import Path
import shutil
import os
import platform
import sys


def log(msg: str):
    print(msg, file=sys.stderr)


# -------------------- Ensure cdxgen is installed --------------------
def ensure_cdxgen():
    """Ensure cdxgen is installed and available in PATH."""
    if shutil.which("cdxgen") or shutil.which("cdxgen.cmd"):
        return

    log("❌ cdxgen not found. Installing globally via npm...")
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
    ensure_cdxgen()

    sbom_file = repo_path / "sbom.json"
    log(f"📦 Generating SBOM in: {repo_path}")

    cmd = ["cdxgen", "-r", "--json-pretty", "-o", str(sbom_file)]
    use_shell = platform.system() == "Windows"

    try:
        subprocess.run(
            cmd,
            cwd=str(repo_path),
            check=True,
            shell=use_shell,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        subprocess.run(
            ["npx", "cdxgen", "-r", "--json-pretty", "-o", str(sbom_file)],
            cwd=str(repo_path),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    log(f"✅ SBOM generated at: {sbom_file}")
    return sbom_file

# -------------------- SIMPLE ORCHESTRATION --------------------
def run_sbom_flow(repo_path) -> Path:
    repo_path = Path(repo_path)

    sbom_file = repo_path / "sbom.json"

    if sbom_file.exists():
        log(f"🔎 sbom.json already exists at: {sbom_file}")
        log("⏩ Skipping SBOM generation.")
        return sbom_file

    log("📦 sbom.json not found — generating SBOM...")
    return generate_sbom(repo_path)
