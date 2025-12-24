import platform
from pathlib import Path
from pydantic import BaseModel
from mcp.types import Tool, TextContent
import logging

from both_supports.os_detect import run_os_detection
from linux_flow.repo_analizer import RepoAnalyzer
from python_flow.lanuage_detector import LanguageDependencyAnalyzer

# ---------------- Input Schema ----------------
class AnalyzeRepoInput(BaseModel):
    repo_path: str
    orchestration_root: str
    report_file: str

# ---------------- Tool Definition ----------------
def get_tool() -> Tool:
    return Tool(
        name="analyze_repo",
        description="Analyze a repository and generate reports based on OS (Linux shell or Python-based).",
        inputSchema=AnalyzeRepoInput.model_json_schema(),
    )

# ---------------- Tool Handler ----------------
async def handle(arguments: dict) -> list[TextContent]:
    data = AnalyzeRepoInput(**arguments)

    repo_path = Path(data.repo_path).resolve()
    orchestration_root = Path(data.orchestration_root).resolve()
    report_file = Path(data.report_file).resolve()

    orchestration_root.mkdir(parents=True, exist_ok=True)

    # Detect OS type
    os_type = run_os_detection()

    if os_type == "linux":
        analyzer = RepoAnalyzer(repo_path=repo_path, report_file=report_file)
        logging.info("Running Linux RepoAnalyzer")
        analyzer.run()
    else:
        analyzer = LanguageDependencyAnalyzer(
            repo_path=repo_path,
            report_file=report_file,
            orchestration_root=orchestration_root
        )
        logging.info("Running LanguageDependencyAnalyzer")
        analyzer.run()

    return [
        TextContent(
            type="text",
            text=f"✅ Repository analysis completed. Report saved at: {report_file}",
            extra={
                "repo_path": str(repo_path),
                "report_file": str(report_file),
                "orchestration_root": str(orchestration_root),
                "os_type": os_type,
            },
        )
    ]