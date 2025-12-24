from pathlib import Path
from pydantic import BaseModel
from mcp.types import Tool, TextContent

from generate_dependency_tree.go import GoDependencyHandler
from generate_dependency_tree.maven import MavenDependencyHandler
from generate_dependency_tree.gradle import GradleDependencyHandler
from generate_dependency_tree.nodejs import NodeDependencyHandler
from generate_dependency_tree.python import PythonDependencyHandler


# ---------------- Input Schema ----------------
class DependencyTreeInput(BaseModel):
    repo_path: str
    output_root: str
    orchestration_root: str
    report_file: str


# ---------------- Tool Definition ----------------
def get_tool() -> Tool:
    return Tool(
        name="generate_dependency_tree",
        description="Extract dependency tree from a repository and write report outside the repo.",
        inputSchema=DependencyTreeInput.model_json_schema(),
    )


# ---------------- Tool Handler ----------------
async def handle(arguments: dict) -> list[TextContent]:
    data = DependencyTreeInput(**arguments)

    repo_path = Path(data.repo_path).resolve()
    orchestration_root = Path(data.orchestration_root).resolve()
    report_file = Path(data.report_file).resolve()

    orchestration_root.mkdir(parents=True, exist_ok=True)

    output_root = orchestration_root

    # ---------------- Safety checks ----------------
    if not repo_path.exists() or not repo_path.is_dir():
        raise ValueError(f"Invalid repo_path: {repo_path}")

    # ---------------- Run extraction ----------------
    handlers = [
        GoDependencyHandler(repo_path=repo_path,output_root=orchestration_root,report_file=report_file),
        MavenDependencyHandler(repo_path=repo_path,output_root=orchestration_root,report_file=report_file),
        GradleDependencyHandler(repo_path=repo_path,output_root=orchestration_root,report_file=report_file),
        NodeDependencyHandler(repo_path=repo_path,output_root=orchestration_root,report_file=report_file),
        PythonDependencyHandler(repo_path=repo_path,output_root=orchestration_root,report_file=report_file),
    ]   
    for handler in handlers:
        handler.run()

    return [
        TextContent(
            type="text",
            text=(
                "✅ Dependency tree extraction completed.\n"
                f"Report saved at: {report_file}"
            ),
            extra={
                "repo_path": str(repo_path),
                "output_root": str(output_root),
                "orchestration_root": str(orchestration_root),
                "report_file": str(report_file),
            },
        )
    ]
