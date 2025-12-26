import asyncio
import json
import logging
from pathlib import Path
from typing import Any
import os

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import httpx
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, CallToolResult, TextContent
from llm.base import BaseLLM

# ----------------------
# Logging setup
# ----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ----------------------
# Configuration
# ----------------------
class Configuration:
    def __init__(self) -> None:
        load_dotenv()

    def load_config(self, file_path: str) -> dict[str, Any]:
        with open(file_path, "r") as f:
            return json.load(f)


# ----------------------
# MCP Server Wrapper
# ----------------------
class MCPServer:
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config
        self.session: ClientSession | None = None
        self.exit_stack = None

    async def initialize(self) -> None:
        from contextlib import AsyncExitStack

        self.exit_stack = AsyncExitStack()
        await self.exit_stack.__aenter__()

        command = self.config["command"]
        args = self.config.get("args", [])
        server_params = StdioServerParameters(command=command, args=args)

        read, write = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self.session = session
        logging.info(f"Initialized server: {self.name}")

    async def list_tools(self) -> list[Tool]:
        assert self.session is not None
        tools_response = await self.session.list_tools()
        tools: list[Tool] = []

        for item in tools_response:
            if isinstance(item, Tool):
                tools.append(item)
            elif isinstance(item, dict):
                tools.append(Tool(**item))
            elif isinstance(item, tuple) and item[0] == "tools":
                for t in item[1]:
                    tools.append(t if isinstance(t, Tool) else Tool(**t))
        return tools

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> CallToolResult:
        assert self.session is not None
        return await self.session.call_tool(tool_name, arguments)

    async def cleanup(self) -> None:
        if self.exit_stack:
            await self.exit_stack.aclose()


# ----------------------
# Chat Session (ORCHESTRATOR)
# ----------------------
class ChatSession:
    def __init__(self, servers: list[MCPServer], llm: BaseLLM) -> None:
        self.servers = servers
        self.llm = llm

        # ✅ MAIN ORCHESTRATION ROOT
        self.analysis_root = Path("mcp_analysis").resolve()
        self.analysis_root.mkdir(exist_ok=True)

        # ✅ SINGLE DEFAULT REPORT FILE (USED BY ALL TOOLS)
        self.report_file = self.analysis_root / "report.json"

        # runtime memory
        self.repo_context: dict[str, Path] = {}

    async def start(self) -> None:
        # ---------------- Init servers ----------------
        for server in self.servers:
            await server.initialize()

        # ---------------- Collect tools ----------------
        all_tools: list[Tool] = []
        for server in self.servers:
            all_tools.extend(await server.list_tools())

        if not all_tools:
            print("❌ No tools available")
            return

        tool_descriptions = "\n".join(
            f"- {t.name}: {t.description}\n"
            f"  Args: {', '.join(t.inputSchema.get('properties', {}).keys())}"
            for t in all_tools
        )

        messages = [{
            "role": "system",
            "content": (
                "You are a helpful assistant.\n\n"
                "IMPORTANT RULES:\n"
                "- 'clone_repo' is ONLY for first-time cloning.\n"
                "- If the user asks for analysis, SBOM generator, or framework information, use 'analyze_repo'.\n"
                "- Some tools have both Linux and Python-based implementations. "
                "- search_frameworks is a tool that searches for frameworks in a repo and generates a reportand otput file as mention like function.\n"
                "- generate_dependency_tree is a tool that generates a dependency tree for a repo and writes the report to a file.\n"
                "Use the if-else logic in the MCP tool handler to decide which implementation to run based on OS detection.\n\n"
                "When a tool is required, respond ONLY with JSON in the following format "
                "and do NOT ask any questions:\n"
                '{"tool": "tool_name", "arguments": {"repo_path": "<repo_path>"}}\n\n'
                f"Available tools:\n{tool_descriptions}"
            ),
        }]

        print("\nAvailable tools:")
        for t in all_tools:
            print(f"- {t.name}")

        # ---------------- Chat loop ----------------
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            messages.append({"role": "user", "content": user_input})
            llm_response = self.llm.get_response(messages)
            print("\nLLM Response:\n", llm_response)

            if not llm_response.startswith("{"):
                continue

            parsed = json.loads(llm_response)
            tool_name = parsed["tool"]
            arguments = parsed.get("arguments", {})

            # -------- GLOBAL PATH INJECTION (SINGLE REPORT FILE) --------
            if tool_name in {"analyze_repo", "extract_sbom_components", "search_frameworks","generate_dependency_tree"}:

                if not self.repo_context:
                    print("❌ No repo available. Clone first.")
                    continue

                repo_path = list(self.repo_context.values())[-1]

                arguments["repo_path"] = str(repo_path)
                arguments["orchestration_root"] = str(self.analysis_root)
                arguments["report_file"] = str(self.report_file)

            # -------- Execute tool --------
            for server in self.servers:
                tools = await server.list_tools()
                if any(t.name == tool_name for t in tools):
                    print(f"\n▶ Executing {tool_name}")
                    result = await server.execute_tool(tool_name, arguments)

                    for content in result.content:
                        if content.type == "text":
                            print(content.text)

                            # ✅ CORRECT repo capture
                            if tool_name == "clone_repo" and content.extra:
                                repo_path = Path(content.extra["repo_path"]).resolve()
                                self.repo_context[repo_path.name] = repo_path
                                print(f"📁 Repo cloned at: {repo_path}")
                    break



# ----------------------
# Main Entry
# ----------------------
async def main():
    config = Configuration()
    servers_config = config.load_config("llm/servers_config.json")

    servers = [MCPServer(name, conf) for name, conf in servers_config["mcpServers"].items()]

    llm_cfg = config.load_config("llm/config.json")
    from llm.factory import get_llm
    llm = get_llm(llm_cfg)
    chat = ChatSession(servers, llm)
    await chat.start()


if __name__ == "__main__":
    asyncio.run(main())
