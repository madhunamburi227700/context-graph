from pathlib import Path
from pydantic import BaseModel
from mcp.types import Tool, TextContent

from both_supports.cdxgen_sbom_generator import run_sbom_flow


# ---------------- Input Schema ----------------
class GenerateSBOMInput(BaseModel):
    repo_path: str


# ---------------- Tool Definition ----------------
def get_tool() -> Tool:
    return Tool(
        name="generate_sbom",
        description="Generate SBOM for a repository using existing SBOM flow.",
        inputSchema=GenerateSBOMInput.model_json_schema(),
    )


# ---------------- Tool Handler ----------------
async def handle(arguments: dict) -> list[TextContent]:
    data = GenerateSBOMInput(**arguments)

    repo_path = Path(data.repo_path).resolve()

    # ---------------- Safety checks ----------------
    if not repo_path.exists() or not repo_path.is_dir():
        raise ValueError(f"Invalid repo_path: {repo_path}")

    # ---------------- Run existing SBOM flow ----------------
    run_sbom_flow(repo_path=repo_path)
    sbom_file = repo_path / "sbom.json"  # define path manually

    # ---------------- Tool Output ----------------
    return [
        TextContent(
            type="text",
            text=(
                "✅ SBOM generation completed.\n"
                f"📁 Repo path: {repo_path}\n"
                f"📄 SBOM file: {sbom_file}"
            ),
            extra={
                "repo_path": str(repo_path),
                "sbom_file": str(sbom_file),
            },
        )
    ]
