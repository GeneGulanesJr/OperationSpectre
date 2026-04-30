"""Core shared logic for OperationSpectre.

Both CLI commands and pi skills import from here.
No subprocess calls -- everything goes through DockerRuntime directly.
All executions are logged for agent review.
"""

from opspectre.core._runtime import get_runtime as get_runtime
from opspectre.core._runtime import reset_runtime as reset_runtime
from opspectre.core.browser_ops import browser_navigate as browser_navigate
from opspectre.core.browser_ops import browser_screenshot as browser_screenshot
from opspectre.core.execution_log import ExecutionEntry as ExecutionEntry
from opspectre.core.execution_log import ExecutionLogger as ExecutionLogger
from opspectre.core.execution_log import exec_logger as exec_logger
from opspectre.core.execution_log import review_run as review_run
from opspectre.core.file_ops import edit_file as edit_file
from opspectre.core.file_ops import list_directory as list_directory
from opspectre.core.file_ops import read_file as read_file
from opspectre.core.file_ops import search_files as search_files
from opspectre.core.file_ops import write_file as write_file
from opspectre.core.sandbox_ops import sandbox_start as sandbox_start
from opspectre.core.sandbox_ops import sandbox_status as sandbox_status
from opspectre.core.sandbox_ops import sandbox_stop as sandbox_stop
from opspectre.core.tools import discover_subdomains as discover_subdomains
from opspectre.core.tools import execute_code as execute_code
from opspectre.core.tools import execute_shell as execute_shell
from opspectre.core.tools import gowitness_capture as gowitness_capture
from opspectre.core.tools import osint_recon as osint_recon
from opspectre.core.tools import port_scan as port_scan
from opspectre.core.tools import probe_http as probe_http
from opspectre.core.tools import run_nmap_scan as run_nmap_scan
from opspectre.core.tools import scan_nuclei as scan_nuclei
from opspectre.core.tools import wpscan_scan as wpscan_scan
