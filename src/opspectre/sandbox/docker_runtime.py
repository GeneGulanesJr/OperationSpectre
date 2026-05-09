import contextlib
import logging
import os
import secrets
import socket
import time
from typing import TYPE_CHECKING, Any, cast

from opspectre.config import Config, ConfigError
from opspectre.performance import performance_logger

# ---------------------------------------------------------------------------
# Lazy imports for optional heavy dependencies
# Importing SandboxError must NOT require ``docker``, ``httpx``, or ``requests``.
# Fallbacks are provided so the module loads even when they are not installed.
# ---------------------------------------------------------------------------
try:
    import httpx as _httpx_mod
except ModuleNotFoundError:
    _httpx_mod = None  # type: ignore[assignment]

try:
    from requests.exceptions import ConnectionError as RequestsConnectionError
    from requests.exceptions import Timeout as RequestsTimeout
except ModuleNotFoundError:
    RequestsConnectionError = ConnectionError  # type: ignore[misc, assignment]
    RequestsTimeout = TimeoutError  # type: ignore[misc, assignment]

# ---------------------------------------------------------------------------
# Lazy docker SDK imports
# Importing SandboxError must NOT require the ``docker`` package.
# The real docker types are resolved at runtime; at import time we provide
# safe fallbacks so the module loads even when docker is not installed.
# ---------------------------------------------------------------------------
try:
    import docker as _docker_mod
    from docker.errors import DockerException as DockerException
    from docker.errors import ImageNotFound as ImageNotFound
    from docker.errors import NotFound as NotFound
    _HAS_DOCKER = True
except ModuleNotFoundError:
    _docker_mod = None  # type: ignore[assignment]
    DockerException = Exception  # type: ignore[misc, assignment]
    ImageNotFound = Exception  # type: ignore[misc, assignment]
    NotFound = Exception  # type: ignore[misc, assignment]
    _HAS_DOCKER = False

if TYPE_CHECKING:
    from docker.models.containers import Container
else:
    Container = Any

_log = logging.getLogger("opspectre.docker_runtime")

HOST_GATEWAY_HOSTNAME = "host.docker.internal"
DOCKER_TIMEOUT = 60
CONTAINER_TOOL_SERVER_PORT = 48081

# Timeout and retry constants
CONTAINER_STOP_TIMEOUT = 5          # seconds to wait before force-killing
CONTAINER_STOP_DELAY = 1            # seconds to wait after removing old container
IMAGE_VERIFY_RETRIES = 3
HEALTH_CHECK_INITIAL_DELAY = 3      # seconds before first health poll
HEALTH_CHECK_RETRIES = 30
HEALTH_CHECK_TIMEOUT = 5            # seconds per health check request
HEALTH_CHECK_POLL_CAP = 5           # max seconds between health polls
DEFAULT_EXECUTION_TIMEOUT = 120     # fallback when config is unreadable
DEFAULT_CONTAINER_PORT_START = 0    # auto-select port


class SandboxError(Exception):
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


def _require_docker() -> Any:
    """Return the docker module, raising a clear error if not installed."""
    if _docker_mod is None:
        raise SandboxError(
            "The 'docker' Python package is required but not installed.",
            "Install it with: pip install docker",
        )
    return _docker_mod

def _require_httpx() -> Any:
    """Return the httpx module, raising a clear error if not installed."""
    if _httpx_mod is None:
        raise SandboxError(
            "The 'httpx' Python package is required but not installed.",
            "Install it with: pip install httpx",
        )
    return _httpx_mod




class DockerRuntime:
    """Manages the lifecycle of the Opspectre sandbox container.

    Handles container creation, health checks, tool-server communication,
    and cleanup via the Docker SDK.
    """

    def __init__(self) -> None:
        """Connect to Docker and auto-detect any running sandbox container."""
        _require_docker()
        self._container: Container | None = None
        self._tool_server_port: int | None = None
        self._tool_server_token: str | None = None

        try:
            self.client = self._connect_docker(max_retries=3)
        except (DockerException, RequestsConnectionError, RequestsTimeout) as e:
            raise SandboxError(
                "Docker is not available",
                "Please ensure Docker Desktop is installed and running.",
            ) from e

        # Auto-detect existing running container
        self._try_reconnect()

    def _connect_docker(self, max_retries: int = 3) -> Any:
        """Connect to Docker daemon with exponential backoff."""
        docker = _require_docker()
        with performance_logger.measure("docker_connect", max_retries=max_retries):
            last_exc: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return docker.from_env(timeout=DOCKER_TIMEOUT)
                except (DockerException, RequestsConnectionError, RequestsTimeout) as e:
                    last_exc = e
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)
            raise last_exc  # type: ignore[misc]

    def _find_available_port(self) -> int:
        """Find and return an available TCP port on the host."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return cast("int", s.getsockname()[1])

    def _resolve_docker_host(self) -> str:
        """Return the host address the Docker daemon is reachable on.

        Parses ``DOCKER_HOST`` for TCP URLs; falls back to ``127.0.0.1``.
        """
        docker_host = os.getenv("DOCKER_HOST", "")
        if docker_host:
            from urllib.parse import urlparse

            parsed = urlparse(docker_host)
            if parsed.scheme in ("tcp", "http", "https") and parsed.hostname:
                return parsed.hostname
        return "127.0.0.1"

    def _try_reconnect(self) -> None:
        """Try to find and reconnect to an existing running container.

        Only reconnects via the opspectre-run-id label to avoid
        accidentally attaching to unrelated containers that may
        happen to have similar environment variables.
        """
        try:
            containers = self.client.containers.list(
                filters={"label": "opspectre-run-id"},
            )
            for container in containers:
                if container.status == "running":
                    self._container = container
                    self._recover_container_state(container)
                    return
        except DockerException as e:
            _log.debug("Failed to reconnect to existing container: %s", e)

    def _recover_container_state(self, container: Container) -> None:
        """Recover port and token from an existing container."""
        try:
            env_list = container.attrs["Config"]["Env"]
            env_dict = {}
            for env_var in env_list:
                k, _, v = env_var.partition("=")
                env_dict[k] = v

            self._tool_server_token = env_dict.get("TOOL_SERVER_TOKEN")

            # Try port bindings first (bridge mode)
            port_bindings = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            port_key = f"{CONTAINER_TOOL_SERVER_PORT}/tcp"
            if port_bindings.get(port_key):
                self._tool_server_port = int(port_bindings[port_key][0]["HostPort"])
            elif "TOOL_SERVER_PORT" in env_dict:
                # Fallback: use env var directly (host network mode)
                self._tool_server_port = int(env_dict["TOOL_SERVER_PORT"])
        except (KeyError, IndexError, TypeError, ValueError) as e:
            _log.debug("Failed to recover container state: %s", e)

    def _verify_image_available(
        self, image_name: str, max_retries: int = IMAGE_VERIFY_RETRIES
    ) -> None:
        """Verify that a Docker image exists locally, retrying on failure."""
        for attempt in range(max_retries):
            try:
                image = self.client.images.get(image_name)
                if not image.id or not image.attrs:
                    raise ImageNotFound(f"Image {image_name} metadata incomplete")
            except (ImageNotFound, DockerException):
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)
            else:
                return

    def _wait_for_tool_server(
        self, max_retries: int = HEALTH_CHECK_RETRIES, timeout: int = HEALTH_CHECK_TIMEOUT
    ) -> None:
        """Poll the tool server health endpoint until it reports healthy."""
        httpx_mod = _require_httpx()
        host = self._resolve_docker_host()
        health_url = f"http://{host}:{self._tool_server_port}/health"

        time.sleep(HEALTH_CHECK_INITIAL_DELAY)

        for attempt in range(max_retries):
            try:
                with httpx_mod.Client(trust_env=False, timeout=timeout) as client:
                    response = client.get(health_url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "healthy":
                            return
            except (
                httpx_mod.ConnectError,
                httpx_mod.TimeoutException,
                httpx_mod.RequestError,
            ) as e:
                _log.debug("Tool server health check attempt %d failed: %s", attempt + 1, e)

            time.sleep(min(2**attempt * 0.5, HEALTH_CHECK_POLL_CAP))

        raise SandboxError(
            "Tool server failed to start",
            "Container initialization timed out. Please try again.",
        )

    def start(self, run_id: str = "default") -> dict[str, Any]:
        """Start a sandbox container. Returns sandbox info dict."""
        container_name = f"opspectre-{run_id}"
        image_name = Config.get("opspectre_image")
        if not image_name:
            raise SandboxError("OPSPECTRE_IMAGE must be configured")

        self._verify_image_available(image_name)

        # Clean up existing container with same name
        with contextlib.suppress(NotFound):
            existing = self.client.containers.get(container_name)
            with contextlib.suppress(Exception):
                existing.stop(timeout=CONTAINER_STOP_TIMEOUT)
            existing.remove(force=True)
            time.sleep(CONTAINER_STOP_DELAY)

        self._tool_server_port = self._find_available_port()
        self._tool_server_token = secrets.token_urlsafe(32)
        try:
            execution_timeout = Config.get_int("opspectre_timeout")
        except ConfigError:
            execution_timeout = DEFAULT_EXECUTION_TIMEOUT

        container = self.client.containers.run(
            image_name,
            command="sleep infinity",
            detach=True,
            name=container_name,
            hostname=container_name,
            ports={f"{CONTAINER_TOOL_SERVER_PORT}/tcp": self._tool_server_port},
            cap_add=["NET_RAW"],
            labels={"opspectre-run-id": run_id},
            environment={
                "PYTHONUNBUFFERED": "1",
                "TOOL_SERVER_PORT": str(CONTAINER_TOOL_SERVER_PORT),
                "TOOL_SERVER_TOKEN": self._tool_server_token,
                "OPSPECTRE_SANDBOX_EXECUTION_TIMEOUT": str(execution_timeout),
                "HOST_GATEWAY": HOST_GATEWAY_HOSTNAME,
            },
            extra_hosts={HOST_GATEWAY_HOSTNAME: "host-gateway"},
            tty=True,
        )

        self._container = container
        self._wait_for_tool_server()

        host = self._resolve_docker_host()
        return {
            "container_id": container.id,
            "container_name": container_name,
            "api_url": f"http://{host}:{self._tool_server_port}",
            "auth_token": self._tool_server_token,
            "tool_server_port": self._tool_server_port,
        }

    def stop(self, run_id: str = "default") -> bool:
        """Stop and remove a sandbox container."""
        container_name = f"opspectre-{run_id}"
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=CONTAINER_STOP_TIMEOUT)
            container.remove()
            self._container = None
            self._tool_server_port = None
            self._tool_server_token = None
            return True
        except (NotFound, DockerException):
            return False

    def status(self, run_id: str = "default") -> str | None:
        """Get container status. Returns 'running', 'stopped', or None."""
        # Prefer the reconnected container (handles compose-launched instances)
        if self._container:
            try:
                self._container.reload()
                return self._container.status
            except DockerException as e:
                _log.debug("Failed to reload container status: %s", e)

        # Fall back to name-based lookup (CLI-started containers)
        container_name = f"opspectre-{run_id}"
        try:
            container = self.client.containers.get(container_name)
            container.reload()
            return container.status
        except (NotFound, DockerException):
            return None

    def execute(self, command: str, timeout: int | None = None) -> dict[str, Any]:
        """Execute a shell command in the container via tool server."""
        if timeout is None:
            try:
                resolved_timeout = Config.get_int("opspectre_timeout")
            except ConfigError:
                resolved_timeout = DEFAULT_EXECUTION_TIMEOUT
        else:
            resolved_timeout = timeout
        result = self._api_post(
            "/execute",
            {"command": command, "timeout": resolved_timeout},
            timeout=resolved_timeout,
        )

        if "error" in result and not result.get("stdout"):
            return {"stdout": "", "stderr": result["error"], "exit_code": -1}

        return {
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code", 0),
        }

    def file_read(self, path: str) -> dict[str, Any]:
        """Read a file from the container."""
        return self._api_post("/file/read", {"path": path})

    def file_write(self, path: str, content: str) -> dict[str, Any]:
        """Write a file to the container."""
        return self._api_post("/file/write", {"path": path, "content": content})

    def file_edit(self, path: str, old_text: str, new_text: str) -> dict[str, Any]:
        """Find and replace in a file."""
        return self._api_post(
            "/file/edit", {"path": path, "old_text": old_text, "new_text": new_text}
        )

    def file_list(self, path: str) -> dict[str, Any]:
        """List files in a directory."""
        return self._api_post("/file/list", {"path": path})

    def file_search(self, query: str, path: str) -> dict[str, Any]:
        """Search file contents."""
        return self._api_post("/file/search", {"pattern": query, "path": path})

    def is_connected(self) -> bool:
        """Return True if a sandbox container is connected and reachable."""
        return self._container is not None and self._tool_server_port is not None

    _API_MAX_RETRIES = 3

    def _api_post(
        self, endpoint: str, payload: dict[str, Any], timeout: int = 30
    ) -> dict[str, Any]:
        """Send an authenticated POST request to the tool server.

        Retries up to _API_MAX_RETRIES times with exponential backoff on
        transient connection errors.
        """
        if not self._tool_server_port or not self._tool_server_token:
            raise SandboxError("No sandbox running. Start one first with 'opspectre sandbox start'")

        host = self._resolve_docker_host()
        api_url = f"http://{host}:{self._tool_server_port}"
        last_exc: Exception | None = None

        for attempt in range(self._API_MAX_RETRIES):
            result = self._try_api_request(api_url, endpoint, payload, timeout)
            if result is not None:
                return result
            last_exc = self._last_api_error
            if attempt < self._API_MAX_RETRIES - 1:
                time.sleep(2**attempt)

        raise SandboxError(
            "Failed to reach tool server after retries",
            str(last_exc) if last_exc else None,
        )

    def _try_api_request(
        self, api_url: str, endpoint: str, payload: dict[str, Any], timeout: int
    ) -> dict[str, Any] | None:
        """Attempt a single API request. Returns result on success, None on transient error.

        Sets self._last_api_error on transient failure. Raises SandboxError on
        non-transient HTTP errors.
        """
        self._last_api_error: Exception | None = None
        try:
            with _require_httpx().Client(trust_env=False, timeout=timeout) as client:
                response = client.post(
                    f"{api_url}{endpoint}",
                    json=payload,
                    headers={"Authorization": f"Bearer {self._tool_server_token}"},
                )
                response.raise_for_status()
                return response.json()
        except (
            _require_httpx().ConnectError,
            _require_httpx().ReadError,
            _require_httpx().WriteError,
        ) as e:
            self._last_api_error = e
            return None
        except _require_httpx().HTTPStatusError as e:
            raise SandboxError(
                f"Tool server error: {e.response.status_code}",
                e.response.text[:200] if e.response.text else None,
            ) from e

    def get_sandbox_info(self) -> dict[str, Any]:
        """Get current sandbox info."""
        if not self._container:
            return {}
        return {
            "container_id": self._container.id,
            "api_url": f"http://{self._resolve_docker_host()}:{self._tool_server_port}",
            "auth_token": self._tool_server_token,
        }
