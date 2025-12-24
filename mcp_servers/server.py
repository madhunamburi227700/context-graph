import sys
import asyncio
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

# Fix import path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Tool Imports
from mcp_servers.tools.git_clone import get_tool as git_clone, handle as git_handler
from mcp_servers.tools.analyzer_repo import get_tool as analysis_repo, handle as repo_analysis
from mcp_servers.tools.sbom import get_tool as sbom_generate, handle as sbom_generate_handler
from mcp_servers.tools.extract_components import get_tool as extract_components, handle as extract_components_handler
from mcp_servers.tools.framework import get_tool as framework_tool, handle as framework_handler
from mcp_servers.tools.tree import get_tool as tree_tool, handle as tree_handler

async def serve():
    server = Server("context-graph-mcp")

    # Tool registry
    TOOLS = {
        "clone_repo": git_handler,
        "analyze_repo": repo_analysis,
        "generate_sbom": sbom_generate_handler,
        "extract_sbom_components": extract_components_handler,
        "search_frameworks": framework_handler,
        "generate_dependency_tree": tree_handler,
    }

    # List tools
    @server.list_tools()
    async def list_tools():
        return [
            git_clone(),
            analysis_repo(),
            sbom_generate(),
            extract_components(),
            framework_tool(),
            tree_tool(),
        ]

    # Call tools
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        handler = TOOLS.get(name)
        if not handler:
            return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
        return await handler(arguments)

    # Run server
    options = server.create_initialization_options()
    async with stdio_server() as (read, write):
        print("✅ Context Graph MCP Server running")
        await server.run(read, write, options)

if __name__ == "__main__":
    asyncio.run(serve())
