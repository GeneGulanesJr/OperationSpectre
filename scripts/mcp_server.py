#!/usr/bin/env python3
"""
OperationSpectre MCP Server Launcher

This script launches the OperationSpectre MCP server with FastAPI for HTTP integration.
"""

import argparse
import logging
import os

# Add the project root to the Python path
import sys
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from opspectre.mcp_server import OperationSpectreMCPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API
class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any]


class MCPResponse(BaseModel):
    success: bool
    data: dict[str, Any]
    error: str | None = None
    stdout: str | None = None
    stderr: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting OperationSpectre MCP Server")

    # Initialize server
    app.state.server = OperationSpectreMCPServer()

    # Test CLI connection
    try:
        status_result = await app.state.server.call_tool("sandbox_status", {})
        if status_result["success"]:
            logger.info("CLI connection successful")
        else:
            logger.warning(f"CLI connection issue: {status_result.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Failed to connect to CLI: {e}")

    yield

    logger.info("Shutting down OperationSpectre MCP Server")


# Create FastAPI app
app = FastAPI(
    title="OperationSpectre MCP Server",
    description="MCP server for OperationSpectre security tools",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "OperationSpectre MCP Server", "version": "1.0.0"}


@app.get("/tools")
async def list_tools():
    """List available tools"""
    server = app.state.server
    return await server.list_tools()


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest) -> MCPResponse:
    """Call a specific tool"""
    server = app.state.server

    try:
        result = await server.call_tool(request.tool_name, request.arguments)
        return MCPResponse(**result)
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OperationSpectre MCP Server"}


def main():
    """Main function to launch the server"""
    parser = argparse.ArgumentParser(
        description="Launch OperationSpectre MCP Server"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Server host (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info(f"Starting OperationSpectre MCP Server on {args.host}:{args.port}")

    # Start server
    uvicorn.run(
        "scripts.mcp_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower()
    )


if __name__ == "__main__":
    main()
