from pathlib import Path
from pydantic import BaseModel
from mcp.types import Tool, TextContent
from both_supports.git_clone import clone_and_checkout

# ---------------- Input Schema ----------------
class CloneRepoInput(BaseModel):
    repo_with_branch: str

# ---------------- Tool Definition ----------------
def get_tool() -> Tool:
    return Tool(
        name="clone_repo",
        description="Clone a git repository into mcp_analysis/<repo_name>",
        inputSchema=CloneRepoInput.model_json_schema(),
    )

# ---------------- Tool Handler ----------------
async def handle(arguments: dict) -> list[TextContent]:
    data = CloneRepoInput(**arguments)

    # Orchestration root is ALWAYS mcp_analysis
    orchestration_root = Path("mcp_analysis").resolve()
    orchestration_root.mkdir(exist_ok=True)

    # Clone repo inside orchestration root
    repo_path = clone_and_checkout(repo_with_branch=data.repo_with_branch, base_dir=orchestration_root)
    repo_path = Path(repo_path).resolve()

    return [
        TextContent(
            type="text",
            text=f"✅ Repository cloned successfully at {repo_path}",
            extra={
                "repo_path": str(repo_path),
                "orchestration_root": str(orchestration_root),
            },
        )
    ]