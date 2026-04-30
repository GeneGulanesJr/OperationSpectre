"""
MCP Server for OperationSpectre

This module provides an MCP server that exposes OperationSpectre functionality
through MCP protocol, allowing AI agents to use the tools directly.
"""

import asyncio
import logging
import secrets
import signal
import sys
from collections.abc import Callable
from typing import Any

from .mcp import MCPToolResult, OperationSpectreMCP, mcp_tools

try:
    from fastapi import FastAPI, HTTPException
except ImportError:
    FastAPI = None  # type: ignore[assignment,misc]
    HTTPException = None  # type: ignore[assignment,misc]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OperationSpectreMCPServer:
    """MCP server for OperationSpectre tools"""

    def __init__(self):
        self.mcp = OperationSpectreMCP()
        self.tools = {tool["name"]: tool for tool in mcp_tools}

        # Dispatch map: tool_name -> (method_name, argument_mapping)
        # Each entry maps incoming argument keys to the MCP method's kwargs.
        self._dispatch: dict[str, Callable[[dict[str, Any]], MCPToolResult]] = {
            "nmap_scan": lambda a: self.mcp.nmap_scan(
                target=a["target"], ports=a.get("ports"), stealth=a.get("stealth", False)
            ),
            "subdomain_discovery": lambda a: self.mcp.subdomain_discovery(
                domain=a["domain"], method=a.get("method", "subfinder")
            ),
            "http_probe": lambda a: self.mcp.http_probe(
                targets=a["targets"], rate_limit=a.get("rate_limit", 5)
            ),
            "file_search": lambda a: self.mcp.file_search(
                pattern=a["pattern"], path=a["path"], recursive=a.get("recursive", True)
            ),
            "file_read": lambda a: self.mcp.file_read(path=a["path"]),
            "file_write": lambda a: self.mcp.file_write(path=a["path"], content=a["content"]),
            "directory_list": lambda a: self.mcp.directory_list(path=a.get("path", "/workspace")),
            "code_execute": lambda a: self.mcp.code_execute(
                language=a.get("language", "python"), code=a["code"]
            ),
            "sandbox_start": lambda a: self.mcp.sandbox_start(),
            "sandbox_stop": lambda a: self.mcp.sandbox_stop(),
            "sandbox_status": lambda a: self.mcp.sandbox_status(),
            "browser_navigate": lambda a: self.mcp.browser_navigate(url=a["url"]),
            "browser_screenshot": lambda a: self.mcp.browser_screenshot(
                url=a["url"],
                output_path=a.get("output_path", "/workspace/output/screenshots/page.png"),
            ),
            "nuclei_scan": lambda a: self.mcp.nuclei_scan(
                targets=a["targets"], severity=a.get("severity", "medium,high,critical")
            ),
            "gowitness_screenshots": lambda a: self.mcp.gowitness_screenshots(
                targets=a["targets"],
                output_dir=a.get("output_dir", "/workspace/output/screenshots"),
            ),
            "osint_passive": lambda a: self.mcp.osint_passive(
                domain=a["domain"], method=a.get("method", "full")
            ),
            "port_scan": lambda a: self.mcp.port_scan(
                target=a["target"],
                scan_type=a.get("scan_type", "quick"),
                ports=a.get("ports"),
            ),
            "wpscan": lambda a: self.mcp.wpscan(url=a["url"]),
            "review_execution_log": lambda a: self.mcp.review_execution_log(
                last_n=a.get("last_n", 50)
            ),
            "read_execution_log": lambda a: self.mcp.read_execution_log(
                last_n=a.get("last_n", 20)
            ),
            "clear_execution_log": lambda a: self.mcp.clear_execution_log(),
        }

    async def list_tools(self) -> dict[str, Any]:
        """List available tools"""
        return {
            "tools": [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "inputSchema": tool["inputSchema"]
                }
                for tool in mcp_tools
            ]
        }

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a specific tool"""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

        # Validate required parameters
        schema = self.tools[tool_name]["inputSchema"]
        for param in schema.get("required", []):
            if param not in arguments:
                return {
                    "success": False,
                    "error": f"Missing required parameter: {param}"
                }

        dispatch_fn = self._dispatch.get(tool_name)
        if dispatch_fn is None:
            return {
                "success": False,
                "error": f"Tool implementation not found: {tool_name}"
            }

        try:
            result = dispatch_fn(arguments)
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global variable for graceful shutdown
server_instance = None


def signal_handler(sig: int, frame: Any) -> None:
    """Handle shutdown signals gracefully.

    Works correctly inside or outside an asyncio event loop.
    """
    print("\nReceived shutdown signal, shutting down gracefully...")
    try:
        loop = asyncio.get_running_loop()
        # We're inside an event loop — stop it cleanly
        loop.stop()
    except RuntimeError:
        # No running loop (e.g. called from main thread before loop starts)
        sys.exit(0)

def create_server() -> OperationSpectreMCPServer:
    """Create and return the MCP server instance"""
    global server_instance
    server_instance = OperationSpectreMCPServer()
    return server_instance


def start_server(host: str = "localhost", port: int = 8000, auth_token: str | None = None):
    """Start the FastAPI server."""
    import uvicorn
    from fastapi import Request
    from fastapi.responses import JSONResponse

    if FastAPI is None:
        print("Error: fastapi and uvicorn are required. Install with: pip install fastapi uvicorn")
        sys.exit(1)

    global server_instance
    server_instance = create_server()

    # Generate or use provided auth token
    token = auth_token or secrets.token_urlsafe(32)
    public_paths = {"/health", "/openapi.json", "/docs"}

    app = FastAPI(title="OperationSpectre MCP Server", version="1.0.0")

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        """Bearer token auth on all endpoints except health/docs."""
        if request.url.path in public_paths or request.url.path.startswith("/docs"):
            return await call_next(request)
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header.removeprefix("Bearer ") != token:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or missing Bearer token."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/tools")
    async def list_tools():
        return {"tools": mcp_tools}

    @app.post("/tools/call")
    async def call_tool(tool_call: dict):
        tool_name = tool_call.get("tool_name")
        arguments = tool_call.get("arguments", {})

        if tool_name not in [tool["name"] for tool in mcp_tools]:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

        result = await server_instance.call_tool(tool_name, arguments)
        return result

    @app.post("/shutdown")
    async def shutdown():
        import os
        import signal
        os.kill(os.getpid(), signal.SIGTERM)
        return {"message": "Shutting down"}

    print(f"Starting OperationSpectre MCP Server on {host}:{port}")
    masked_token = token[:6] + "..." + token[-4:] if len(token) > 12 else "***"
    print(f"Auth token (masked): {masked_token}")
    print(f"Health check: http://{host}:{port}/health")
    print(f"Tools list: http://{host}:{port}/tools")
    print(f"Tools endpoint: http://{host}:{port}/tools/call")
    print("\nExample authenticated call:")
    print(f'  curl -H "Authorization: Bearer {masked_token}" http://{host}:{port}/health')

    uvicorn.run(app, host=host, port=port)


# Standalone server execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OperationSpectre MCP Server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    parser.add_argument("--auth-token", default=None, help="Auth token (auto-generated if omitted)")

    args = parser.parse_args()

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the FastAPI server (creates server instance internally)
    start_server(args.host, args.port, auth_token=args.auth_token)
