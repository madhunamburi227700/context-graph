from pathlib import Path
from pydantic import BaseModel
from mcp.types import Tool, TextContent
import logging

from both_supports.os_detect import run_os_detection
from python_flow.windows_search_framework import orchestrate_python_framework_search
from linux_flow.search_framework import orchestrate_linux_framework_search


# ---------------- Input Schema ----------------
class SearchFrameworksInput(BaseModel):
    repo_path: str
    output_file: str
    orchestration_root: str
    report_file: str


# ---------------- Tool Definition ----------------
def get_tool() -> Tool:
    return Tool(
        name="search_frameworks",
        description="Search frameworks from SBOM output and codebase and write results into a single report.json.",
        inputSchema=SearchFrameworksInput.model_json_schema(),
    )


# ---------------- Tool Handler ----------------
async def handle(arguments: dict) -> list[TextContent]:
    data = SearchFrameworksInput(**arguments)

    repo_path = Path(data.repo_path).resolve()
    orchestration_root = Path(data.orchestration_root).resolve()
    report_file = Path(data.report_file).resolve()

    orchestration_root.mkdir(parents=True, exist_ok=True)

    # ✅ Standard intermediate output file (INTERNAL ONLY)
    sbom_output_file = orchestration_root / "output.txt"

    # ---------------- Safety checks ----------------
    if not repo_path.exists() or not repo_path.is_dir():
        raise ValueError(f"Invalid repo_path: {repo_path}")

    # Detect OS
    os_type = run_os_detection()

    # ---------------- Execute search ----------------
    if os_type == "linux":
        logging.info("Searching frameworks using Linux flow")
        orchestrate_linux_framework_search(
            repo_path=repo_path,
            output_file=sbom_output_file,
            report_file=report_file,
        )
    else:
        logging.info("Searching frameworks using Python flow")
        orchestrate_python_framework_search(
            repo_path=repo_path,
            output_file=sbom_output_file,
            report_file=report_file,
        )

    return [
        TextContent(
            type="text",
            text=f"✅ Framework search completed.\nReport saved at: {report_file}",
            extra={
                "repo_path": str(repo_path),
                "orchestration_root": str(orchestration_root),
                "report_file": str(report_file),
                "sbom_output_file": str(sbom_output_file),
            },
        )
    ]
