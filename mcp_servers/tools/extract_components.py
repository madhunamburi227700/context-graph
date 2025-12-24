from pathlib import Path
from pydantic import BaseModel
from mcp.types import Tool, TextContent

from both_supports.retrieve_components import orchestrate_sbom


# ---------------- Input Schema ----------------
class ExtractSBOMComponentsInput(BaseModel):
    repo_path: str
    orchestration_root: str | None = None
    report_file: str | None = None


# ---------------- Tool Definition ----------------
def get_tool() -> Tool:
    return Tool(
        name="extract_sbom_components",
        description="Extract SBOM components from sbom.json and write report outside the repo.",
        inputSchema=ExtractSBOMComponentsInput.model_json_schema(),
    )


# ---------------- Tool Handler ----------------
async def handle(arguments: dict) -> list[TextContent]:
    data = ExtractSBOMComponentsInput(**arguments)

    repo_path = Path(data.repo_path).resolve()
    orchestration_root = Path(data.orchestration_root).resolve()
    report_file = Path(data.report_file).resolve()

    orchestration_root.mkdir(parents=True, exist_ok=True)

    # ---------------- Safety checks ----------------
    if not repo_path.exists() or not repo_path.is_dir():
        raise ValueError(f"Invalid repo_path: {repo_path}")

    # ---------------- Run extraction ----------------
    orchestrate_sbom(
        repo_path=repo_path,
        orchestration_root=orchestration_root,
        report_file=report_file,
    )

    return [
        TextContent(
            type="text",
            text=(
                "✅ SBOM components extraction completed.\n"
                f"Report saved at: {report_file}"
            ),
            extra={
                "repo_path": str(repo_path),
                "orchestration_root": str(orchestration_root),
                "report_file": str(report_file),
            },
        )
    ]
