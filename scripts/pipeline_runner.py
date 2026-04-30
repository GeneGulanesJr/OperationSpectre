#!/usr/bin/env python3
"""
OperationSpectre Pipeline Runner
=================================
Runs a multi-step security pipeline by spawning a fresh pi RPC subprocess
for each step. Each worker gets a clean context — the 9B model never
accumulates tool output across steps.

Usage:
    python3 scripts/pipeline_runner.py pipelines/ctf-web.yaml --target http://10.10.10.10
    python3 scripts/pipeline_runner.py pipelines/ctf-crypto.yaml --input "ZmxhZ3toZWxsb30="
    python3 scripts/pipeline_runner.py pipelines/pentest.yaml --target example.com

Architecture:
    Manager (this script) — pure Python, no LLM context
    ├── Reads pipeline YAML
    ├── Resolves dependencies (topological sort)
    ├── For each step:
    │   ├── Injects previous step summaries into prompt
    │   ├── Spawns: pi --mode rpc --no-session
    │   ├── Sends prompt via RPC JSON protocol
    │   ├── Waits for agent_end event
    │   ├── Extracts assistant text → saves to results/
    │   └── Kills subprocess → context fully freed
    └── Final step: assembles report from all summaries
"""

import argparse
import asyncio
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Try to import yaml, fall back to basic parser
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


# ── YAML Loading ─────────────────────────────────────────────────

def load_yaml(path: str) -> dict[str, Any]:
    """Load a pipeline YAML file."""
    with open(path) as f:
        if yaml:
            return yaml.safe_load(f)
        # Minimal fallback — just error out with helpful message
        print("[ERROR] PyYAML not installed. Run: pip install pyyaml")
        sys.exit(1)


# ── Variable Resolution ─────────────────────────────────────────

def resolve_variables(pipeline: dict[str, Any], cli_args: argparse.Namespace) -> dict[str, str]:
    """Merge pipeline defaults with CLI overrides."""
    variables = dict(pipeline.get("variables", {}))

    if cli_args.target:
        variables["TARGET"] = cli_args.target
        if not variables.get("DOMAIN"):
            variables["DOMAIN"] = _extract_domain(cli_args.target)

    if cli_args.input_data:
        variables["INPUT"] = cli_args.input_data

    if cli_args.output_dir:
        variables["OUTPUT_DIR"] = cli_args.output_dir

    variables["TIMESTAMP"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    return variables


def _extract_domain(target: str) -> str:
    """Extract hostname from a target URL, falling back to the raw string."""
    try:
        parsed = urlparse(target if "://" in target else f"http://{target}")
        return parsed.hostname or target
    except Exception:
        return target


def apply_variables(text: str, variables: dict[str, str]) -> str:
    """Replace {VAR} placeholders in text."""
    for key, value in variables.items():
        text = text.replace(f"{{{key}}}", str(value))
    return text


# ── Dependency Resolution (Topological Sort) ────────────────────

def resolve_order(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Topological sort of steps based on depends_on."""
    step_map = {s["id"]: s for s in steps}
    visited = set()
    order = []

    def visit(step_id: str) -> None:
        if step_id in visited:
            return
        visited.add(step_id)
        step = step_map[step_id]
        for dep in step.get("depends_on", []):
            visit(dep)
        order.append(step)

    for step in steps:
        visit(step["id"])

    return order


# ── RPC Client ──────────────────────────────────────────────────

class PiWorker:
    """Spawn a fresh pi RPC subprocess, send one prompt, get the result."""

    def __init__(self, model: str | None = None, provider: str | None = None, timeout: int = 300):
        self.model = model
        self.provider = provider
        self.timeout = timeout
        self.proc: subprocess.Popen | None = None

    def _start(self) -> None:
        """Spawn a fresh pi --mode rpc --no-session subprocess."""
        cmd = ["pi", "--mode", "rpc", "--no-session"]
        if self.model:
            cmd.extend(["--model", self.model])
        if self.provider:
            cmd.extend(["--provider", self.provider])

        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        self._read_until_ready()

    def _read_until_ready(self) -> None:
        """Read lines until we get a response indicating pi is ready."""
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "response":
                    return
            except json.JSONDecodeError:
                continue
            break

    def run(self, prompt: str, system_hint: str = "") -> str:
        """Send a prompt and return the assistant's text response."""
        try:
            self._start()
        except Exception as e:
            return f"[ERROR] Failed to start pi subprocess: {e}"

        assert self.proc and self.proc.stdin and self.proc.stdout

        full_prompt = self._build_prompt(prompt, system_hint)
        self._send_prompt(full_prompt)
        assistant_text = self._collect_response()
        self._stop()
        return assistant_text

    def _build_prompt(self, prompt: str, system_hint: str) -> str:
        """Combine system hint and user prompt into a single message."""
        if system_hint:
            return f"{system_hint}\n\n---\n\n{prompt}"
        return prompt

    def _send_prompt(self, full_prompt: str) -> None:
        """Send the prompt to the pi subprocess via stdin."""
        assert self.proc and self.proc.stdin
        cmd = {"type": "prompt", "message": full_prompt}
        self.proc.stdin.write(json.dumps(cmd) + "\n")
        self.proc.stdin.flush()

    def _collect_response(self) -> str:
        """Collect events until agent_end or timeout. Returns assistant text."""
        assert self.proc and self.proc.stdout
        assistant_text = ""
        start_time = time.time()

        for line in self.proc.stdout:
            if time.time() - start_time > self.timeout:
                assistant_text += "\n[TIMEOUT] Step exceeded time limit."
                break

            line = line.strip()
            if not line:
                continue

            event = self._parse_event(line)
            if event is None:
                continue

            event_type = event.get("type")

            if event_type == "message_update":
                assistant_text += self._extract_delta(event)

            if event_type == "agent_end":
                assistant_text = self._extract_agent_end_text(event, assistant_text)
                break

        return assistant_text.strip() or "[No response from pi]"

    def _parse_event(self, line: str) -> dict[str, Any] | None:
        """Parse a JSON event line. Returns None on parse failure."""
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None

    def _extract_delta(self, event: dict[str, Any]) -> str:
        """Extract streaming text delta from a message_update event."""
        delta = event.get("assistantMessageEvent", {})
        if delta.get("type") == "text_delta":
            return delta.get("delta", "")
        return ""

    def _extract_agent_end_text(self, event: dict[str, Any], fallback: str) -> str:
        """Extract the final assistant text from an agent_end event."""
        messages = event.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", "")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block.get("text", fallback)
            elif isinstance(content, str):
                return content
            break
        return fallback

    def _stop(self) -> None:
        """Kill the subprocess."""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                    self.proc.wait(timeout=2)
                except Exception:
                    pass
            self.proc = None


# ── Pipeline Execution (Sequential) ─────────────────────────────

def _print_pipeline_header(pipeline_name: str, variables: dict[str, str], steps: list, output_dir: Path) -> None:
    """Print the pipeline banner."""
    print("=" * 60)
    print(f"  PIPELINE: {pipeline_name}")
    print(f"  TARGET:   {variables.get('TARGET', variables.get('INPUT', 'N/A'))}")
    print(f"  STEPS:    {len(steps)}")
    print(f"  OUTPUT:   {output_dir}")
    print("=" * 60)
    print()


def _check_step_deps(step: dict[str, Any], failed_steps: list[str]) -> list[str]:
    """Return list of failed dependency IDs for this step."""
    deps = step.get("depends_on", [])
    return [d for d in deps if d in failed_steps]


def _build_step_prompt(step: dict[str, Any], variables: dict[str, str], is_report: bool) -> str:
    """Build the prompt for a step, appending command if present."""
    prompt = apply_variables(step.get("prompt", ""), variables)
    command = step.get("command")
    if command and not is_report:
        command = apply_variables(command, variables)
        prompt += f"\n\nCommand to run: {command}"
    return prompt


def _run_single_step(step: dict[str, Any], cli_args: argparse.Namespace, system_hint: str) -> str:
    """Run a single step through PiWorker and return the result."""
    prompt = _build_step_prompt(step, {}, step.get("is_report", False))
    # Rebuild with actual variables passed through caller
    worker = PiWorker(
        model=cli_args.model,
        provider=cli_args.provider,
        timeout=cli_args.step_timeout,
    )
    return worker.run(prompt, system_hint)


def _save_step_output(step_id: str, result: str, results_dir: Path) -> None:
    """Save a step result to the summaries directory."""
    summary_file = results_dir / f"{step_id}.txt"
    summary_file.write_text(result, encoding="utf-8")


def _print_step_result(step_name: str, elapsed: float, result: str) -> None:
    """Print truncated step result to console."""
    display_result = result[:500] + ("..." if len(result) > 500 else "")
    print(f"  Completed in {elapsed:.1f}s")
    print(f"  Result: {display_result}")
    print()


def _save_report(output_dir: Path, result: str) -> None:
    """Save the final report to REPORT.md."""
    report_file = output_dir / "REPORT.md"
    report_file.write_text(result, encoding="utf-8")
    print(f"  📄 Report saved to: {report_file}")
    print()


def _print_pipeline_footer(completed: int, failed: int, output_dir: Path) -> None:
    """Print the pipeline completion summary."""
    print("=" * 60)
    print("  PIPELINE COMPLETE")
    print(f"  Steps:  {completed} completed, {failed} failed")
    print(f"  Output: {output_dir}")
    print("=" * 60)


def run_pipeline(pipeline_path: str, cli_args: argparse.Namespace) -> None:
    """Execute the full pipeline sequentially."""
    pipeline = load_yaml(pipeline_path)
    variables = resolve_variables(pipeline, cli_args)
    steps = resolve_order(pipeline.get("steps", []))

    pipeline_name = pipeline.get("name", "Unnamed Pipeline")
    output_dir = Path(variables.get("OUTPUT_DIR", "/workspace/output/pipeline"))
    results_dir = output_dir / "summaries"
    results_dir.mkdir(parents=True, exist_ok=True)

    _print_pipeline_header(pipeline_name, variables, steps, output_dir)

    completed_summaries: dict[str, str] = {}
    failed_steps: list[str] = []

    for i, step in enumerate(steps, 1):
        step_id = step["id"]
        step_name = step.get("name", step_id)
        is_report = step.get("is_report", False)

        print(f"[{i}/{len(steps)}] {step_name} (id: {step_id})")
        print("-" * 40)

        failed_deps = _check_step_deps(step, failed_steps)
        if failed_deps:
            msg = f"SKIP — dependencies failed: {', '.join(failed_deps)}"
            print(f"  {msg}")
            completed_summaries[step_id] = msg
            failed_steps.append(step_id)
            continue

        system_hint = build_system_hint(step, completed_summaries, step.get("depends_on", []), variables, is_report)
        prompt = _build_step_prompt(step, variables, is_report)

        worker = PiWorker(
            model=cli_args.model,
            provider=cli_args.provider,
            timeout=cli_args.step_timeout,
        )

        start_time = time.time()
        result = worker.run(prompt, system_hint)
        elapsed = time.time() - start_time

        _save_step_output(step_id, result, results_dir)
        _print_step_result(step_name, elapsed, result)
        completed_summaries[step_id] = result

        if is_report:
            _save_report(output_dir, result)

    _print_pipeline_footer(len(completed_summaries), len(failed_steps), output_dir)

    report_file = output_dir / "REPORT.md"
    if report_file.exists():
        print()
        print(report_file.read_text())


def build_system_hint(
    step: dict[str, Any],
    completed: dict[str, str],
    deps: list[str],
    variables: dict[str, str],
    is_report: bool,
) -> str:
    """Build a system-level context injection for the worker."""
    parts = []

    if is_report:
        parts.append("You are generating a final report. Here are the results from all previous steps:\n")
        for step_id, summary in completed.items():
            truncated = summary[:2000] + ("..." if len(summary) > 2000 else "")
            parts.append(f"### {step_id}\n{truncated}\n")
    else:
        parts.append("You are a security testing assistant. Run the requested tool/command and output ONLY a concise summary.")
        parts.append("Keep your response under 30 lines. Save detailed output to files, summarize key findings.\n")

        if deps:
            parts.append("Previous step results:")
            for dep in deps:
                if dep in completed:
                    truncated = completed[dep][:1500] + ("..." if len(completed[dep]) > 1500 else "")
                    parts.append(f"### {dep}\n{truncated}\n")

    return "\n".join(parts)


# ── CLI ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="OperationSpectre Pipeline Runner — fully automated multi-step pipelines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # CTF web challenge
  python3 scripts/pipeline_runner.py pipelines/ctf-web.yaml --target http://10.10.10.10:8080

  # CTF crypto challenge
  python3 scripts/pipeline_runner.py pipelines/ctf-crypto.yaml --input "ZmxhZ3toZWxsb30="

  # Full pentest
  python3 scripts/pipeline_runner.py pipelines/pentest.yaml --target example.com

  # Parallel execution (faster)
  python3 scripts/pipeline_runner.py pipelines/pentest.yaml --target example.com --parallel

  # With specific model
  python3 scripts/pipeline_runner.py pipelines/ctf-web.yaml --target http://10.10.10.10 --model local/llama3:9b
        """,
    )

    parser.add_argument("pipeline", help="Path to pipeline YAML file")
    parser.add_argument("--target", "-t", help="Target URL or IP")
    parser.add_argument("--input", "-i", dest="input_data", help="Input data (for crypto etc.)")
    parser.add_argument("--output-dir", "-o", help="Override output directory")
    parser.add_argument("--model", "-m", help="Model pattern for pi (e.g., 'local/llama3:9b')")
    parser.add_argument("--provider", "-p", help="Provider for pi (e.g., 'ollama')")
    parser.add_argument("--step-timeout", type=int, default=300, help="Timeout per step in seconds (default: 300)")
    parser.add_argument("--parallel", action="store_true", help="Run independent steps in parallel for faster execution")

    args = parser.parse_args()

    if not Path(args.pipeline).exists():
        print(f"[ERROR] Pipeline file not found: {args.pipeline}")
        sys.exit(1)

    if args.parallel:
        print("Running pipeline in parallel mode...")
        runner = PipelineRunner(
            model=args.model,
            provider=args.provider,
            step_timeout=args.step_timeout,
        )
        asyncio.run(runner.run_pipeline(args.pipeline, args))
    else:
        run_pipeline(args.pipeline, args)


# ── PARALLEL PIPELINE RUNNER ──────────────────────────────────────

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStep:
    id: str
    name: str
    prompt: str
    command: str | None
    depends_on: list[str]
    is_report: bool
    status: StepStatus = StepStatus.PENDING
    result: str = ""
    start_time: float = 0
    end_time: float = 0
    error: str = ""


class PipelineRunner:
    """Parallel pipeline execution manager."""

    def __init__(self, model: str | None = None, provider: str | None = None, step_timeout: int = 300):
        self.model = model
        self.provider = provider
        self.step_timeout = step_timeout
        self.steps: dict[str, PipelineStep] = {}
        self.completed_summaries: dict[str, str] = {}
        self.failed_steps: set[str] = set()
        self.semaphore = asyncio.Semaphore(5)

    def load_pipeline(self, pipeline_path: str, cli_args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, str]]:
        """Load and parse the pipeline configuration."""
        pipeline = load_yaml(pipeline_path)
        variables = resolve_variables(pipeline, cli_args)

        for step in pipeline.get("steps", []):
            self.steps[step["id"]] = PipelineStep(
                id=step["id"],
                name=step.get("name", step["id"]),
                prompt=step.get("prompt", ""),
                command=step.get("command", ""),
                depends_on=step.get("depends_on", []),
                is_report=step.get("is_report", False),
                status=StepStatus.PENDING,
            )

        return pipeline, variables

    def _get_ready_steps(self) -> list[PipelineStep]:
        """Get steps whose dependencies are all completed."""
        return [
            step for step in self.steps.values()
            if step.status == StepStatus.PENDING
            and all(dep in self.completed_summaries for dep in step.depends_on)
        ]

    def _propagate_failures(self) -> bool:
        """Mark steps with failed deps as failed. Returns True if any were marked."""
        made_progress = False
        for step in self.steps.values():
            if step.status != StepStatus.PENDING:
                continue
            failed_deps = [d for d in step.depends_on if d in self.failed_steps]
            if failed_deps:
                step.status = StepStatus.FAILED
                step.error = f"Skipped — dependencies failed: {', '.join(failed_deps)}"
                self.failed_steps.add(step.id)
                step.end_time = time.time()
                made_progress = True
        return made_progress

    async def _execute_step(self, step: PipelineStep, variables: dict[str, str]) -> None:
        """Execute a single pipeline step with timeout handling."""
        async with self.semaphore:
            step.status = StepStatus.RUNNING
            step.start_time = time.time()

            try:
                prompt = apply_variables(step.prompt, variables)
                if step.command and not step.is_report:
                    command = apply_variables(step.command, variables)
                    prompt += f"\n\nCommand to run: {command}"

                system_hint = self._build_system_hint(step, variables)

                result = await asyncio.wait_for(
                    self._run_step_worker(prompt, system_hint),
                    timeout=self.step_timeout,
                )

                step.result = result
                step.status = StepStatus.COMPLETED
                step.end_time = time.time()
                self.completed_summaries[step.id] = result

            except TimeoutError:
                self._mark_step_failed(step, f"Step timed out after {self.step_timeout} seconds")

            except Exception as e:
                self._mark_step_failed(step, str(e))

    def _mark_step_failed(self, step: PipelineStep, error: str) -> None:
        """Mark a step as failed and record the error."""
        step.status = StepStatus.FAILED
        step.error = error
        self.failed_steps.add(step.id)
        step.end_time = time.time()

    def _build_system_hint(self, step: PipelineStep, variables: dict[str, str]) -> str:
        """Build system hint with previous results for context."""
        parts = ["Previous results:"]

        for dep_id in step.depends_on:
            if dep_id in self.completed_summaries:
                parts.append(f"\n{dep_id} result: {self.completed_summaries[dep_id][:200]}...")

        parts.append(f"\nCurrent target: {variables.get('TARGET', 'N/A')}")
        return "\n".join(parts)

    async def _run_step_worker(self, prompt: str, system_hint: str) -> str:
        """Run a step in a worker process."""
        worker = PiWorker(
            model=self.model,
            provider=self.provider,
            timeout=self.step_timeout,
        )
        return worker.run(prompt, system_hint)

    def _save_step_result(self, step: PipelineStep, output_dir: Path) -> None:
        """Save step result to file."""
        results_dir = output_dir / "summaries"
        results_dir.mkdir(parents=True, exist_ok=True)
        summary_file = results_dir / f"{step.id}.txt"
        summary_file.write_text(step.result, encoding="utf-8")

    def _tally_progress(self, counted: set[str]) -> tuple[int, int]:
        """Print newly completed/failed steps. Returns (new_completed, new_failed)."""
        new_completed = 0
        new_failed = 0
        for step in self.steps.values():
            if step.id in counted:
                continue
            if step.status == StepStatus.COMPLETED:
                self._save_step_result(step, self._output_dir)
                elapsed = step.end_time - step.start_time
                print(f"✓ {step.name} completed in {elapsed:.1f}s")
                new_completed += 1
                counted.add(step.id)
            elif step.status == StepStatus.FAILED:
                print(f"✗ {step.name} failed: {step.error}")
                new_failed += 1
                counted.add(step.id)
        return new_completed, new_failed

    def _find_report_step(self) -> PipelineStep | None:
        """Find the report step if one exists."""
        for step in self.steps.values():
            if step.is_report:
                return step
        return None

    async def _generate_report(self, report_step: PipelineStep, variables: dict[str, str], output_dir: Path) -> None:
        """Generate and save the final report."""
        print("\nGenerating final report...")
        await self._execute_step(report_step, variables)
        self._save_step_result(report_step, output_dir)
        report_file = output_dir / "REPORT.md"
        report_file.write_text(report_step.result, encoding="utf-8")
        print(f"📄 Final report saved to: {report_file}")

    def _print_header(self, pipeline: dict[str, Any], variables: dict[str, str], output_dir: Path) -> None:
        """Print pipeline run header."""
        print("=" * 60)
        print(f"  PARALLEL PIPELINE: {pipeline.get('name', 'Unnamed Pipeline')}")
        print(f"  TARGET: {variables.get('TARGET', variables.get('INPUT', 'N/A'))}")
        print(f"  TOTAL STEPS: {len(self.steps)}")
        print(f"  OUTPUT: {output_dir}")
        print("=" * 60)
        print()

    def _print_summary(self, completed: int, failed: int, output_dir: Path) -> None:
        """Print final summary."""
        print("\n" + "=" * 60)
        print("  PARALLEL PIPELINE COMPLETE")
        print(f"  Steps: {completed} completed, {failed} failed")
        print(f"  Output: {output_dir}")
        print("=" * 60)

    async def run_pipeline(self, pipeline_path: str, cli_args: argparse.Namespace) -> None:
        """Execute the pipeline with parallel processing."""
        pipeline, variables = self.load_pipeline(pipeline_path, cli_args)

        output_dir = Path(variables.get("OUTPUT_DIR", "/workspace/output/parallel-pipeline"))
        self._output_dir = output_dir
        results_dir = output_dir / "summaries"
        results_dir.mkdir(parents=True, exist_ok=True)

        self._print_header(pipeline, variables, output_dir)

        completed_count = 0
        failed_count = 0
        counted_steps: set[str] = set()

        while completed_count + failed_count < len(self.steps):
            ready_steps = self._get_ready_steps()

            if not ready_steps:
                if not self._propagate_failures():
                    time.sleep(1)
                continue

            tasks = [self._execute_step(step, variables) for step in ready_steps]
            print(f"Executing {len(tasks)} steps concurrently...")
            await asyncio.gather(*tasks, return_exceptions=True)

            new_done, new_fail = self._tally_progress(counted_steps)
            completed_count += new_done
            failed_count += new_fail

        report_step = self._find_report_step()
        if report_step:
            await self._generate_report(report_step, variables, output_dir)

        self._print_summary(completed_count, failed_count, output_dir)

        if report_step:
            print("\n" + report_step.result)


if __name__ == "__main__":
    main()
