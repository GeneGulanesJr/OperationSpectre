"""MCP Tools for OperationSpectre — Direct Core Integration

This module provides MCP tools that call core functions directly,
eliminating subprocess overhead. Both CLI and MCP share the same core logic.
"""

from dataclasses import dataclass
from typing import Any

from opspectre.core import (
    browser_navigate,
    browser_screenshot,
    discover_subdomains,
    exec_logger,
    execute_code,
    gowitness_capture,
    list_directory,
    osint_recon,
    port_scan,
    probe_http,
    review_run,
    run_nmap_scan,
    sandbox_start,
    sandbox_status,
    sandbox_stop,
    scan_nuclei,
    search_files,
    wpscan_scan,
)
from opspectre.core import (
    read_file as core_file_read,
)
from opspectre.core import (
    write_file as core_file_write,
)


@dataclass
class MCPToolResult:
    """Structured result from MCP tool execution."""
    success: bool
    data: dict[str, Any]
    error: str | None = None
    stdout: str | None = None
    stderr: str | None = None


def _to_mcp_result(core_result: dict) -> MCPToolResult:
    """Convert core function result to MCPToolResult."""
    return MCPToolResult(
        success=core_result.get("success", False),
        data=core_result.get("data", {}),
        error=core_result.get("error"),
        stdout=core_result.get("stdout"),
        stderr=core_result.get("stderr"),
    )


class OperationSpectreMCP:
    """MCP tools that call core functions directly — no subprocess overhead."""

    def nmap_scan(
        self, target: str,
        ports: str | None = None,
        stealth: bool = False,
    ) -> MCPToolResult:
        """Run nmap scan with structured output.

        Args:
            target: Target host (IP or domain)
            ports: Port specification (e.g., "80,443", "1-1000")
            stealth: Use stealth scanning mode
        """
        result = run_nmap_scan(target, ports=ports, stealth=stealth)
        return _to_mcp_result(result)

    def subdomain_discovery(self, domain: str, method: str = "subfinder") -> MCPToolResult:
        """Find subdomains using specified method.

        Args:
            domain: Target domain
            method: Discovery method (subfinder, crt, full_passive)
        """
        result = discover_subdomains(domain, method=method)
        return _to_mcp_result(result)

    def http_probe(self, targets: str | list[str], rate_limit: int = 5) -> MCPToolResult:
        """Probe HTTP targets with status codes and headers.

        Args:
            targets: Single target or list of targets
            rate_limit: Request rate limit
        """
        result = probe_http(targets, rate_limit=rate_limit)
        return _to_mcp_result(result)

    def file_search(self, pattern: str, path: str, recursive: bool = True) -> MCPToolResult:
        """Search file contents.

        Args:
            pattern: Search pattern (regex supported)
            path: Directory or file path to search
            recursive: Search recursively in directories
        """
        result = search_files(pattern, path, recursive=recursive)
        return _to_mcp_result(result)

    def file_read(self, path: str) -> MCPToolResult:
        """Read file contents.

        Args:
            path: File path to read
        """
        result = core_file_read(path)
        return _to_mcp_result(result)

    def file_write(self, path: str, content: str) -> MCPToolResult:
        """Write content to file.

        Args:
            path: File path to write
            content: Content to write
        """
        result = core_file_write(path, content)
        return _to_mcp_result(result)

    def directory_list(self, path: str = "/workspace") -> MCPToolResult:
        """List directory contents.

        Args:
            path: Directory path to list
        """
        result = list_directory(path)
        return _to_mcp_result(result)

    def code_execute(self, language: str, code: str) -> MCPToolResult:
        """Execute code in sandbox.

        Args:
            language: Programming language (python, node)
            code: Code to execute
        """
        result = execute_code(language, code)
        return _to_mcp_result(result)

    def sandbox_start(self) -> MCPToolResult:
        """Start the sandbox container."""
        result = sandbox_start()
        return _to_mcp_result(result)

    def sandbox_stop(self) -> MCPToolResult:
        """Stop the sandbox container."""
        result = sandbox_stop()
        return _to_mcp_result(result)

    def sandbox_status(self) -> MCPToolResult:
        """Get sandbox status."""
        result = sandbox_status()
        return _to_mcp_result(result)

    def browser_navigate(self, url: str) -> MCPToolResult:
        """Navigate browser to URL and get accessibility tree.

        Args:
            url: URL to navigate to
        """
        result = browser_navigate(url)
        return _to_mcp_result(result)

    def browser_screenshot(
        self, url: str, output_path: str = "/workspace/output/screenshots/page.png"
    ) -> MCPToolResult:
        """Take a full-page screenshot of a URL.

        Args:
            url: URL to navigate to and screenshot.
            output_path: Path to save the screenshot inside the sandbox.
        """
        result = browser_screenshot(url, output_path=output_path)
        return _to_mcp_result(result)

    def nuclei_scan(
        self,
        targets: str | list[str],
        severity: str = "medium,high,critical",
    ) -> MCPToolResult:
        """Run vulnerability scanning with Nuclei.

        Args:
            targets: Target URLs or file with targets
            severity: Severity levels (low,medium,high,critical)
        """
        result = scan_nuclei(targets, severity=severity)
        return _to_mcp_result(result)

    def gowitness_screenshots(
        self,
        targets: str | list[str],
        output_dir: str = "/workspace/output/screenshots",
    ) -> MCPToolResult:
        """Take screenshots of targets using gowitness.

        Args:
            targets: Target URLs or file with targets
            output_dir: Directory to save screenshots
        """
        result = gowitness_capture(targets, output_dir=output_dir)
        return _to_mcp_result(result)

    def osint_passive(self, domain: str, method: str = "full") -> MCPToolResult:
        """Run passive OSINT reconnaissance.

        Args:
            domain: Target domain
            method: OSINT method (ct, wayback, google, shodan, full)
        """
        result = osint_recon(domain, method=method)
        return _to_mcp_result(result)

    def port_scan(
        self,
        target: str,
        scan_type: str = "quick",
        ports: str | None = None,
    ) -> MCPToolResult:
        """Run port scan with different scan types.

        Args:
            target: Target host
            scan_type: Scan type (quick, full, stealth, service)
            ports: Custom port specification
        """
        result = port_scan(target, scan_type=scan_type, ports=ports)
        return _to_mcp_result(result)

    def wpscan(self, url: str) -> MCPToolResult:
        """WordPress vulnerability scan.

        Args:
            url: WordPress site URL
        """
        result = wpscan_scan(url)
        return _to_mcp_result(result)

    def review_execution_log(self, last_n: int = 50) -> MCPToolResult:
        """Review execution log and get actionable suggestions.

        Call this BEFORE generating a report to identify failures,
        empty results, and retry opportunities.

        Args:
            last_n: Number of recent entries to analyze (default 50)
        """
        entries = exec_logger.read_all(last_n=last_n)
        review = review_run(entries)
        return _to_mcp_result({
            "success": True,
            "data": review,
            "error": None,
        })

    def read_execution_log(self, last_n: int = 20) -> MCPToolResult:
        """Read raw execution log entries.

        Args:
            last_n: Number of recent entries to return (default 20)
        """
        entries = exec_logger.read_all(last_n=last_n)
        return _to_mcp_result({
            "success": True,
            "data": {"entries": entries, "count": len(entries)},
            "error": None,
        })

    def clear_execution_log(self) -> MCPToolResult:
        """Clear the execution log file."""
        count = exec_logger.clear()
        return _to_mcp_result({
            "success": True,
            "data": {"cleared_entries": count},
            "error": None,
        })


# Global instance
_opspectre_mcp = OperationSpectreMCP()


# MCP tool definitions
mcp_tools = [
    {
        "name": "nmap_scan",
        "description": "Run nmap port scan with service detection",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target host (IP address or domain name)"
                },
                "ports": {
                    "type": "string",
                    "description": "Port specification (e.g., '80,443', '1-1000', '8080')"
                },
                "stealth": {
                    "type": "boolean",
                    "description": "Use stealth scanning mode (slower but less detectable)",
                    "default": False
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "subdomain_discovery",
        "description": "Discover subdomains using various methods",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Target domain for subdomain discovery"
                },
                "method": {
                    "type": "string",
                    "description": "Discovery method: subfinder, crt, full_passive",
                    "default": "subfinder",
                    "enum": ["subfinder", "crt", "full_passive"]
                }
            },
            "required": ["domain"]
        }
    },
    {
        "name": "http_probe",
        "description": "Probe HTTP targets to check responsiveness and gather headers",
        "inputSchema": {
            "type": "object",
            "properties": {
                "targets": {
                    "type": ["string", "array"],
                    "description": "Single target URL or list of target URLs"
                },
                "rate_limit": {
                    "type": "integer",
                    "description": "Rate limit in requests per second",
                    "default": 5
                }
            },
            "required": ["targets"]
        }
    },
    {
        "name": "file_search",
        "description": "Search file contents for patterns",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (supports regex)"
                },
                "path": {
                    "type": "string",
                    "description": "Directory or file path to search"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Search recursively in directories",
                    "default": True
                }
            },
            "required": ["pattern", "path"]
        }
    },
    {
        "name": "file_read",
        "description": "Read file contents",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to read"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "file_write",
        "description": "Write content to a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "directory_list",
        "description": "List directory contents",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list",
                    "default": "/workspace"
                }
            }
        }
    },
    {
        "name": "code_execute",
        "description": "Execute code in the sandbox",
        "inputSchema": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "Programming language",
                    "enum": ["python", "node"],
                    "default": "python"
                },
                "code": {
                    "type": "string",
                    "description": "Code to execute"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "sandbox_start",
        "description": "Start the OperationSpectre sandbox container",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "sandbox_stop",
        "description": "Stop the OperationSpectre sandbox container",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "sandbox_status",
        "description": "Get the status of the OperationSpectre sandbox",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "browser_navigate",
        "description": "Navigate browser to a URL and get accessibility tree",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to navigate to"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "browser_screenshot",
        "description": "Take a full-page screenshot of a URL using Playwright",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to navigate to and screenshot"
                },
                "output_path": {
                    "type": "string",
                    "description": "Path to save the screenshot inside the sandbox",
                    "default": "/workspace/output/screenshots/page.png"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "nuclei_scan",
        "description": "Run vulnerability scanning with Nuclei",
        "inputSchema": {
            "type": "object",
            "properties": {
                "targets": {
                    "type": ["string", "array"],
                    "description": "Target URLs or file with targets"
                },
                "severity": {
                    "type": "string",
                    "description": "Severity levels to scan (low,medium,high,critical)",
                    "default": "medium,high,critical"
                }
            },
            "required": ["targets"]
        }
    },
    {
        "name": "gowitness_screenshots",
        "description": "Take screenshots of multiple targets using gowitness",
        "inputSchema": {
            "type": "object",
            "properties": {
                "targets": {
                    "type": ["string", "array"],
                    "description": "Target URLs or file with targets"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save screenshots",
                    "default": "/workspace/output/screenshots"
                }
            },
            "required": ["targets"]
        }
    },
    {
        "name": "osint_passive",
        "description": "Run passive OSINT reconnaissance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Target domain for OSINT"
                },
                "method": {
                    "type": "string",
                    "description": "OSINT method: ct, wayback, google, shodan, full",
                    "default": "full",
                    "enum": ["ct", "wayback", "google", "shodan", "full"]
                }
            },
            "required": ["domain"]
        }
    },
    {
        "name": "port_scan",
        "description": "Run port scan with different scan profiles",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target host"
                },
                "scan_type": {
                    "type": "string",
                    "description": "Scan type: quick, full, stealth, service",
                    "default": "quick",
                    "enum": ["quick", "full", "stealth", "service"]
                },
                "ports": {
                    "type": "string",
                    "description": "Custom port specification"
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "wpscan",
        "description": "WordPress vulnerability scan",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "WordPress site URL"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "review_execution_log",
        "description": (
            "Review execution log before generating a report. "
            "Returns failures, empty results, slow ops, and retry suggestions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "last_n": {
                    "type": "integer",
                    "description": "Number of recent entries to analyze",
                    "default": 50
                }
            }
        }
    },
    {
        "name": "read_execution_log",
        "description": "Read raw execution log entries",
        "inputSchema": {
            "type": "object",
            "properties": {
                "last_n": {
                    "type": "integer",
                    "description": "Number of recent entries to return",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "clear_execution_log",
        "description": "Clear the execution log file",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]
