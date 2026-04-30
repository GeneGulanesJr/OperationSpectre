/**
 * OperationSpectre Sandbox Extension
 *
 * Routes pi's built-in tools (bash, read, write, edit) to the
 * OperationSpectre Docker sandbox container. When the container is
 * running, all tool operations execute inside the Kali-based sandbox
 * with the full security toolchain.
 *
 * Container detection:
 *   1. Finds "opspectre-full" container via Docker API
 *   2. Recovers tool-server port + token from container env vars
 *   3. Falls back to docker exec for bash, tool-server HTTP API for files
 *
 * Commands:
 *   /sandbox          — Show connection status
 *   /sandbox start    — Start the sandbox via docker compose
 *   /sandbox stop     — Stop the sandbox
 *   /sandbox connect  — Reconnect to a running container
 *   /sandbox local    — Disconnect, use local tools
 */

import { spawn } from "node:child_process";
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, resolve, dirname, posix } from "node:path";
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import {
	type BashOperations,
	type ReadOperations,
	type WriteOperations,
	type EditOperations,
	createBashTool,
	createReadTool,
	createWriteTool,
	createEditTool,
	truncateHead,
	DEFAULT_MAX_BYTES,
	DEFAULT_MAX_LINES,
} from "@mariozechner/pi-coding-agent";
import { Type } from "typebox";

// ─── Types ──────────────────────────────────────────────────────────

interface SandboxConnection {
	containerId: string;
	containerName: string;
	port: number;
	token: string;
	host: string;
}

// ─── Constants ──────────────────────────────────────────────────────

const CONTAINER_NAME = "opspectre-full";
const TOOL_SERVER_PORT_ENV = "TOOL_SERVER_PORT";
const TOOL_SERVER_TOKEN_ENV = "TOOL_SERVER_TOKEN";
const DEFAULT_PORT = 48081;
const CONTAINER_WORKSPACE = "/workspace";

// ─── Docker exec helpers ────────────────────────────────────────────

function dockerExec(
	container: string,
	command: string,
	options?: { timeout?: number },
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
	return new Promise((resolve, reject) => {
		const args = ["exec", container, "bash", "-c", command];
		const child = spawn("docker", args, {
			stdio: ["ignore", "pipe", "pipe"],
		});

		let timedOut = false;
		let timer: NodeJS.Timeout | undefined;

		if (options?.timeout) {
			timer = setTimeout(() => {
				timedOut = true;
				child.kill("SIGKILL");
			}, options.timeout * 1000);
		}

		const chunks: Buffer[] = [];
		const errChunks: Buffer[] = [];

		child.stdout.on("data", (d: Buffer) => chunks.push(d));
		child.stderr.on("data", (d: Buffer) => errChunks.push(d));

		child.on("error", (err) => {
			if (timer) clearTimeout(timer);
			// Docker not found (ENOENT) — reject with a clear message instead of crashing
			reject(new Error(`Docker is not available: ${err.message}. Ensure Docker Desktop is running and docker is in your PATH.`));
		});

		child.on("close", (code) => {
			if (timer) clearTimeout(timer);
			if (timedOut) {
				reject(new Error(`Command timed out after ${options!.timeout}s`));
			} else {
				resolve({
					stdout: Buffer.concat(chunks).toString("utf-8"),
					stderr: Buffer.concat(errChunks).toString("utf-8"),
					exitCode: code ?? 1,
				});
			}
		});
	});
}

async function dockerInspect(container: string): Promise<Record<string, string> | null> {
	const result = await dockerSpawn(["inspect", "--format", "{{json .Config.Env}}", container]);
	if (!result || result.exitCode !== 0) return null;
	try {
		const envArr = JSON.parse(result.stdout) as string[];
		const envDict: Record<string, string> = {};
		for (const entry of envArr) {
			const [k, ...rest] = entry.split("=");
			envDict[k] = rest.join("=");
		}
		return envDict;
	} catch {
		return null;
	}
}

function dockerSpawn(args: string[], options?: { stdin?: "pipe" | "ignore" }): Promise<{ stdout: string; stderr: string; exitCode: number | null } | null> {
	return new Promise((resolve) => {
		const child = spawn("docker", args, {
			stdio: [options?.stdin ?? "ignore", "pipe", "pipe"],
		});
		const chunks: Buffer[] = [];
		const errChunks: Buffer[] = [];
		child.stdout.on("data", (d: Buffer) => chunks.push(d));
		child.stderr.on("data", (d: Buffer) => errChunks.push(d));
		child.on("error", (err) => {
			// Docker not found (ENOENT) or other spawn errors — return null gracefully
			resolve(null);
		});
		child.on("close", (code) => {
			resolve({
				stdout: Buffer.concat(chunks).toString("utf-8"),
				stderr: Buffer.concat(errChunks).toString("utf-8"),
				exitCode: code,
			});
		});
	});
}

async function isContainerRunning(container: string): Promise<boolean> {
	const result = await dockerSpawn(["inspect", "--format", "{{.State.Running}}", container]);
	if (!result || result.exitCode !== 0) return false;
	return result.stdout.trim() === "true";
}

async function dockerComposeUp(composePath: string): Promise<number> {
	const result = await dockerSpawn(["compose", "-f", composePath, "up", "-d"], { stdin: "pipe" });
	return result?.exitCode ?? 1;
}

async function dockerComposeStop(composePath: string): Promise<number> {
	const result = await dockerSpawn(["compose", "-f", composePath, "down"], { stdin: "pipe" });
	return result?.exitCode ?? 1;
}

// ─── Tool-server HTTP helpers ───────────────────────────────────────

async function toolServerPost<T = unknown>(
	conn: SandboxConnection,
	endpoint: string,
	body: Record<string, unknown>,
	timeout = 30_000,
): Promise<T> {
	const url = `http://${conn.host}:${conn.port}${endpoint}`;
	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), timeout);

	try {
		const response = await fetch(url, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${conn.token}`,
			},
			body: JSON.stringify(body),
			signal: controller.signal,
		});
		if (!response.ok) {
			throw new Error(`Tool server ${response.status}: ${await response.text()}`);
		}
		return (await response.json()) as T;
	} finally {
		clearTimeout(timer);
	}
}

// ─── Remote operations factories ────────────────────────────────────

function createContainerBashOps(
	container: string,
	localCwd: string,
	remoteCwd: string,
): BashOperations {
	return {
		async exec(command, cwd, { onData, signal, timeout }) {
			const effectiveCwd = cwd === localCwd ? remoteCwd : cwd;
			const wrapped = `cd ${JSON.stringify(effectiveCwd)} 2>/dev/null; ${command}`;

			return new Promise((resolve, reject) => {
				const child = spawn("docker", ["exec", container, "bash", "-c", wrapped], {
					stdio: ["ignore", "pipe", "pipe"],
				});

				let timedOut = false;
				let timer: NodeJS.Timeout | undefined;

				if (timeout && timeout > 0) {
					timer = setTimeout(() => {
						timedOut = true;
						try { process.kill(-child.pid!); } catch { child.kill("SIGKILL"); }
					}, timeout * 1000);
				}

				child.stdout.on("data", (d: Buffer) => onData(d));
				child.stderr.on("data", (d: Buffer) => onData(d));

				child.on("error", (err) => {
					if (timer) clearTimeout(timer);
					reject(err);
				});

				const onAbort = () => {
					try { process.kill(-child.pid!); } catch { child.kill("SIGKILL"); }
				};
				signal?.addEventListener("abort", onAbort, { once: true });

				child.on("close", (code) => {
					if (timer) clearTimeout(timer);
					signal?.removeEventListener("abort", onAbort);
					if (signal?.aborted) reject(new Error("aborted"));
					else if (timedOut) reject(new Error(`timeout:${timeout}`));
					else resolve({ exitCode: code });
				});
			});
		},
	};
}

function createContainerReadOps(
	container: string,
	localCwd: string,
	remoteCwd: string,
): ReadOperations {
	const toRemote = (p: string) => {
		if (p.startsWith(localCwd)) return p.replace(localCwd, remoteCwd);
		if (p.startsWith("/")) return p;
		return posix.join(remoteCwd, p);
	};

	return {
		async readFile(path) {
			const remotePath = toRemote(path);
			const result = await dockerExec(container, `cat ${JSON.stringify(remotePath)}`);
			if (result.exitCode !== 0) {
				throw new Error(`Failed to read ${remotePath}: ${result.stderr}`);
			}
			return result.stdout;
		},
		async access(path) {
			const remotePath = toRemote(path);
			const result = await dockerExec(container, `test -e ${JSON.stringify(remotePath)}`);
			if (result.exitCode !== 0) throw new Error("Not found");
		},
		async detectImageMimeType(path) {
			const remotePath = toRemote(path);
			try {
				const result = await dockerExec(container, `file --mime-type -b ${JSON.stringify(remotePath)}`);
				if (result.exitCode !== 0) return null;
				const mime = result.stdout.trim();
				const supported = ["image/jpeg", "image/png", "image/gif", "image/webp"];
				return supported.includes(mime) ? mime : null;
			} catch {
				return null;
			}
		},
	};
}

function createContainerWriteOps(
	container: string,
	localCwd: string,
	remoteCwd: string,
): WriteOperations {
	const toRemote = (p: string) => {
		if (p.startsWith(localCwd)) return p.replace(localCwd, remoteCwd);
		if (p.startsWith("/")) return p;
		return posix.join(remoteCwd, p);
	};

	return {
		async writeFile(path, content) {
			const remotePath = toRemote(path);
			const b64 = Buffer.from(content).toString("base64");
			const cmd = `mkdir -p ${JSON.stringify(dirname(remotePath))} && echo ${JSON.stringify(b64)} | base64 -d > ${JSON.stringify(remotePath)}`;
			const result = await dockerExec(container, cmd);
			if (result.exitCode !== 0) {
				throw new Error(`Failed to write ${remotePath}: ${result.stderr}`);
			}
		},
		async mkdir(dir) {
			const remoteDir = toRemote(dir);
			const result = await dockerExec(container, `mkdir -p ${JSON.stringify(remoteDir)}`);
			if (result.exitCode !== 0) {
				throw new Error(`Failed to mkdir ${remoteDir}: ${result.stderr}`);
			}
		},
	};
}

function createContainerEditOps(
	container: string,
	localCwd: string,
	remoteCwd: string,
): EditOperations {
	const readOps = createContainerReadOps(container, localCwd, remoteCwd);
	const writeOps = createContainerWriteOps(container, localCwd, remoteCwd);
	return {
		readFile: readOps.readFile,
		access: readOps.access,
		writeFile: writeOps.writeFile,
	};
}

// ─── Connection discovery ───────────────────────────────────────────

async function discoverConnection(): Promise<SandboxConnection | null> {
	const running = await isContainerRunning(CONTAINER_NAME);
	if (!running) return null;

	const env = await dockerInspect(CONTAINER_NAME);
	if (!env) return null;

	const port = parseInt(env[TOOL_SERVER_PORT_ENV] || String(DEFAULT_PORT), 10);
	const token = env[TOOL_SERVER_TOKEN_ENV] || "";
	const host = "127.0.0.1";

	return {
		containerId: CONTAINER_NAME,
		containerName: CONTAINER_NAME,
		port,
		token,
		host,
	};
}

// ─── Extension ──────────────────────────────────────────────────────

export default function (pi: ExtensionAPI) {
	const localCwd = process.cwd();
	const remoteCwd = CONTAINER_WORKSPACE;

	// Create local tool instances as fallback
	const localBash = createBashTool(localCwd);
	const localRead = createReadTool(localCwd);
	const localWrite = createWriteTool(localCwd);
	const localEdit = createEditTool(localCwd);

	let connection: SandboxConnection | null = null;
	let connected = false;
	let forceLocal = false;

	const isConnected = () => connected && connection !== null;

	// ─── Bash override ────────────────────────────────────────────

	pi.registerTool({
		...localBash,
		label: "bash",
		promptSnippet: "Execute shell commands (routed to OperationSpectre sandbox when connected)",
		promptGuidelines: [
			"When the OperationSpectre sandbox is connected, all bash commands execute inside the Kali container with the full security toolchain (nmap, nuclei, sqlmap, metasploit, etc.).",
			"Security tool commands like nmap, nuclei, sqlmap, hydra, ffuf, subfinder, httpx, gowitness, trivy should be run directly — the sandbox has them installed.",
			"Output from sandbox commands is saved under /workspace/output/ which maps to the local ./output/ directory.",
		],
		async execute(id, params, signal, onUpdate, ctx) {
			if (isConnected()) {
				try {
					const sandboxBash = createBashTool(localCwd, {
						operations: createContainerBashOps(CONTAINER_NAME, localCwd, remoteCwd),
					});
					return await sandboxBash.execute(id, params, signal, onUpdate);
				} catch (err) {
					// If container exec fails, fall through to local
					const msg = err instanceof Error ? err.message : String(err);
					if (msg.includes("No such container") || msg.includes("is not running")) {
						connected = false;
						connection = null;
						ctx.ui.notify("⚠️ Sandbox lost — falling back to local tools", "warning");
						updateStatus(ctx);
					} else {
						throw err;
					}
				}
			}
			return localBash.execute(id, params, signal, onUpdate);
		},
	});

	// ─── Read override ────────────────────────────────────────────

	pi.registerTool({
		...localRead,
		label: "read",
		async execute(id, params, signal, onUpdate, ctx) {
			if (isConnected()) {
				try {
					const sandboxRead = createReadTool(localCwd, {
						operations: createContainerReadOps(CONTAINER_NAME, localCwd, remoteCwd),
					});
					return await sandboxRead.execute(id, params, signal, onUpdate);
				} catch (err) {
					const msg = err instanceof Error ? err.message : String(err);
					if (msg.includes("is not running") || msg.includes("Not found")) {
						// Fall through to local for non-sandbox files
					} else {
						throw err;
					}
				}
			}
			return localRead.execute(id, params, signal, onUpdate);
		},
	});

	// ─── Write override ───────────────────────────────────────────

	pi.registerTool({
		...localWrite,
		label: "write",
		async execute(id, params, signal, onUpdate, ctx) {
			if (isConnected()) {
				try {
					const sandboxWrite = createWriteTool(localCwd, {
						operations: createContainerWriteOps(CONTAINER_NAME, localCwd, remoteCwd),
					});
					return await sandboxWrite.execute(id, params, signal, onUpdate);
				} catch (err) {
					const msg = err instanceof Error ? err.message : String(err);
					if (msg.includes("is not running")) {
						connected = false;
						connection = null;
						ctx.ui.notify("⚠️ Sandbox lost — falling back to local tools", "warning");
						updateStatus(ctx);
					} else {
						throw err;
					}
				}
			}
			return localWrite.execute(id, params, signal, onUpdate);
		},
	});

	// ─── Edit override ────────────────────────────────────────────

	pi.registerTool({
		...localEdit,
		label: "edit",
		async execute(id, params, signal, onUpdate, ctx) {
			if (isConnected()) {
				try {
					const sandboxEdit = createEditTool(localCwd, {
						operations: createContainerEditOps(CONTAINER_NAME, localCwd, remoteCwd),
					});
					return await sandboxEdit.execute(id, params, signal, onUpdate);
				} catch (err) {
					const msg = err instanceof Error ? err.message : String(err);
					if (msg.includes("is not running")) {
						connected = false;
						connection = null;
						ctx.ui.notify("⚠️ Sandbox lost — falling back to local tools", "warning");
						updateStatus(ctx);
					} else {
						throw err;
					}
				}
			}
			return localEdit.execute(id, params, signal, onUpdate);
		},
	});

	// ─── Custom tool: sandbox_exec ────────────────────────────────

	pi.registerTool({
		name: "sandbox_exec",
		label: "Sandbox Exec",
		description:
			"Execute a command explicitly in the OperationSpectre sandbox container. " +
			"Use when you need guaranteed sandbox execution with timeout control. " +
			"Returns stdout, stderr, and exit code.",
		promptSnippet: "Run a command in the OperationSpectre Kali sandbox",
		parameters: Type.Object({
			command: Type.String({ description: "Shell command to execute in the sandbox" }),
			timeout: Type.Optional(Type.Number({ description: "Timeout in seconds (default: 120, max: 600)", minimum: 1, maximum: 600 })),
		}),
		async execute(_id, params, _signal, _onUpdate, ctx) {
			if (!isConnected()) {
				throw new Error("Sandbox is not connected. Use /sandbox start or /sandbox connect.");
			}

			const timeout = Math.min(params.timeout ?? 120, 600);
			const result = await dockerExec(CONTAINER_NAME, params.command, { timeout });

			let output = "";
			if (result.stdout) output += result.stdout;
			if (result.stderr) output += (output ? "\n" : "") + result.stderr;

			const truncation = truncateHead(output, {
				maxLines: DEFAULT_MAX_LINES,
				maxBytes: DEFAULT_MAX_BYTES,
			});

			let text = truncation.content;
			if (truncation.truncated) {
				text += `\n\n[Output truncated: ${truncation.outputLines} of ${truncation.totalLines} lines shown]`;
			}

			if (result.exitCode !== 0) {
				text += `\n[Exit code: ${result.exitCode}]`;
			}

			return {
				content: [{ type: "text", text }],
				details: {
					exitCode: result.exitCode,
					truncated: truncation.truncated,
				},
			};
		},
	});

	// ─── Custom tool: sandbox_status ──────────────────────────────

	pi.registerTool({
		name: "sandbox_status",
		label: "Sandbox Status",
		description: "Check the OperationSpectre sandbox container status and connection info.",
		parameters: Type.Object({}),
		async execute() {
			if (!isConnected()) {
				const running = await isContainerRunning(CONTAINER_NAME);
				return {
					content: [{
						type: "text",
						text: running
							? `Container "${CONTAINER_NAME}" is running but not connected. Use /sandbox connect.`
							: `Container "${CONTAINER_NAME}" is not running. Use /sandbox start.`,
					}],
					details: { connected: false, containerRunning: running },
				};
			}

			// Quick health check
			let healthy = false;
			try {
				const result = await dockerExec(CONTAINER_NAME, "curl -sf http://127.0.0.1:48081/health");
				healthy = result.exitCode === 0;
			} catch {
				healthy = false;
			}

			return {
				content: [{
					type: "text",
					text: [
						`🛡️ OperationSpectre Sandbox`,
						`  Container: ${connection.containerName}`,
						`  Status: ${healthy ? "healthy" : "running (tool server may be starting)"}`,
						`  Tool Server: http://${connection.host}:${connection.port}`,
						`  Workspace: ${remoteCwd} → ${localCwd}/output/`,
					].join("\n"),
				}],
				details: {
					connected: true,
					healthy,
					container: connection.containerName,
					port: connection.port,
				},
			};
		},
	});

	// ─── Status bar helper ────────────────────────────────────────

	function updateStatus(ctx: { ui: ExtensionAPI extends (pi: infer P) => void ? never : P ; ui: any }) {
		const ui = (ctx as any).ui;
		if (!ui) return;

		if (forceLocal) {
			ui.setStatus("opspectre", ui.theme.fg("dim", "○ Sandbox: local mode"));
		} else if (isConnected()) {
			ui.setStatus("opspectre", ui.theme.fg("success", "🛡️ Sandbox: connected"));
		} else {
			ui.setStatus("opspectre", ui.theme.fg("warning", "⚠️ Sandbox: offline"));
		}
	}

	// ─── /sandbox command ─────────────────────────────────────────

	pi.registerCommand("sandbox", {
		description: "Manage the OperationSpectre Docker sandbox",
		getArgumentCompletions(prefix: string) {
			const cmds = ["start", "stop", "connect", "disconnect", "local", "status"];
			return cmds
				.filter((c) => c.startsWith(prefix))
				.map((c) => ({ value: c, label: c }));
		},
		async handler(args, ctx) {
			const sub = args.trim().toLowerCase();

			switch (sub) {
				case "start": {
					ctx.ui.notify("Starting sandbox container...", "info");
					const composePath = join(localCwd, "containers", "docker-compose.yml");

					if (!existsSync(composePath)) {
						ctx.ui.notify("docker-compose.yml not found at containers/docker-compose.yml", "error");
						return;
					}

					const code = await dockerComposeUp(composePath);
					if (code !== 0) {
						ctx.ui.notify(`Failed to start sandbox (exit code ${code})`, "error");
						return;
					}

					// Wait for container to be ready
					ctx.ui.notify("Waiting for container to initialize...", "info");
					for (let i = 0; i < 30; i++) {
						await new Promise((r) => setTimeout(r, 2000));
						const conn = await discoverConnection();
						if (conn) {
							connection = conn;
							connected = true;
							forceLocal = false;
							updateStatus({ ui: ctx.ui });
							ctx.ui.notify("🛡️ Sandbox started and connected!", "success");
							return;
						}
					}
					ctx.ui.notify("Container started but tool server not detected. Try /sandbox connect.", "warning");
					break;
				}

				case "stop": {
					ctx.ui.notify("Stopping sandbox container...", "info");
					const composePath = join(localCwd, "containers", "docker-compose.yml");
					const code = await dockerComposeStop(composePath);
					connection = null;
					connected = false;
					forceLocal = false;
					updateStatus({ ui: ctx.ui });
					if (code === 0) {
						ctx.ui.notify("Sandbox stopped.", "success");
					} else {
						ctx.ui.notify(`Stop command returned ${code}`, "warning");
					}
					break;
				}

				case "connect": {
					ctx.ui.notify("Connecting to sandbox...", "info");
					const conn = await discoverConnection();
					if (conn) {
						connection = conn;
						connected = true;
						forceLocal = false;
						updateStatus({ ui: ctx.ui });
						ctx.ui.notify(`🛡️ Connected to sandbox (port ${conn.port})`, "success");
					} else {
						const running = await isContainerRunning(CONTAINER_NAME);
						if (running) {
							ctx.ui.notify("Container is running but tool server not detected. Check container logs.", "error");
						} else {
							ctx.ui.notify("Container is not running. Use /sandbox start first.", "error");
						}
					}
					break;
				}

				case "disconnect":
				case "local": {
					forceLocal = sub === "local";
					connection = null;
					connected = false;
					updateStatus({ ui: ctx.ui });
					ctx.ui.notify(
						forceLocal ? "Switched to local mode (sandbox disabled for this session)" : "Disconnected from sandbox",
						"info",
					);
					break;
				}

				case "status":
				default: {
					if (isConnected()) {
						let healthy = false;
						try {
							const r = await dockerExec(CONTAINER_NAME, "curl -sf http://127.0.0.1:48081/health");
							healthy = r.exitCode === 0;
						} catch { /* not healthy */ }

						const lines = [
							`🛡️  OperationSpectre Sandbox Status`,
							`  Container:  ${connection!.containerName}`,
							`  Connected:  yes`,
							`  Healthy:    ${healthy ? "yes" : "checking..."}`,
							`  Tool Server: http://${connection!.host}:${connection!.port}`,
							`  Workspace:  ${remoteCwd} → ./output/`,
							`  Mode:       tools routed to sandbox`,
						];
						ctx.ui.notify(lines.join("\n"), "info");
					} else {
						const running = await isContainerRunning(CONTAINER_NAME);
						const lines = [
							`⚠️  OperationSpectre Sandbox Status`,
							`  Container:  ${running ? "running" : "stopped"}`,
							`  Connected:  no`,
							`  Mode:       local tools`,
							``,
							`  Commands: /sandbox start | stop | connect | disconnect | local`,
						];
						ctx.ui.notify(lines.join("\n"), "info");
					}
					break;
				}
			}
		},
	});

	// ─── Session lifecycle ────────────────────────────────────────

	pi.on("session_start", async (_event, ctx) => {
		if (forceLocal) {
			updateStatus({ ui: ctx.ui });
			ctx.ui.notify("Sandbox: local mode (use /sandbox connect to enable)", "info");
			return;
		}

		// Auto-discover running sandbox
		const conn = await discoverConnection();
		if (conn) {
			connection = conn;
			connected = true;
			updateStatus({ ui: ctx.ui });
			ctx.ui.notify(`🛡️ Sandbox connected (port ${conn.port})`, "success");
		} else {
			connected = false;
			connection = null;
			updateStatus({ ui: ctx.ui });
			const running = await isContainerRunning(CONTAINER_NAME);
			if (running) {
				ctx.ui.notify("Sandbox container is running but not fully ready. Try /sandbox connect.", "warning");
			} else {
				ctx.ui.notify("Sandbox offline. Use /sandbox start to begin.", "info");
			}
		}
	});

	// ─── Modify system prompt to mention sandbox ──────────────────

	pi.on("before_agent_start", async (event) => {
		if (isConnected()) {
			const sandboxInfo = [
				"",
				"## OperationSpectre Sandbox",
				`Your bash/read/write/edit tools are routed to the **${CONTAINER_NAME}** Docker container (Kali-based).`,
				"The sandbox contains the full security toolchain: nmap, nuclei, sqlmap, metasploit, hydra, ffuf, subfinder, httpx, gowitness, trivy, wpscan, burpsuite, john, hashcat, and more.",
				"Playbooks are auto-loaded in bash: rate-limit helpers ($RL_*), OSINT playbook, scan helpers.",
				"Save all output under /workspace/output/ (mapped to ./output/ on host).",
				"Use /sandbox to check status or manage the container.",
				"",
			].join("\n");

			return {
				systemPrompt: event.systemPrompt + sandboxInfo,
			};
		}
	});

	// ─── Handle user bash commands ────────────────────────────────

	pi.on("user_bash", () => {
		if (!isConnected()) return;
		return {
			operations: createContainerBashOps(CONTAINER_NAME, localCwd, remoteCwd),
		};
	});
}
