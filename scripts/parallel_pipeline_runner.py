#!/usr/bin/env python3
"""
Parallel Pipeline Runner - Executes pipeline steps concurrently where possible
Usage: python3 scripts/parallel_pipeline_runner.py pipelines/pentest.yaml --target example.com
"""

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


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
    command: str
    depends_on: list[str]
    is_report: bool
    status: StepStatus = StepStatus.PENDING
    result: str = ""
    start_time: float = 0
    end_time: float = 0
    error: str = ""


class ParallelPipelineRunner:
    def __init__(self, model: str = "default", provider: str = "default", step_timeout: int = 300):
        self.model = model
        self.provider = provider
        self.step_timeout = step_timeout
        self.steps: dict[str, PipelineStep] = {}
        self.completed_summaries: dict[str, str] = {}
        self.failed_steps: set[str] = set()
        self.semaphore = asyncio.Semaphore(5)

    def load_pipeline(self, pipeline_path: str, cli_args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, str]]:
        """Load and parse the pipeline configuration."""
        with open(pipeline_path) as f:
            pipeline = yaml.safe_load(f)

        variables = self._resolve_variables(pipeline, cli_args)

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

    def _resolve_variables(self, pipeline: dict[str, Any], cli_args: argparse.Namespace) -> dict[str, str]:
        """Resolve pipeline variables from CLI arguments and environment."""
        variables = {
            "TARGET": getattr(cli_args, 'target', ''),
            "DOMAIN": getattr(cli_args, 'domain', ''),
            "OUTPUT_DIR": "/workspace/output/parallel-pipeline",
        }

        if hasattr(cli_args, 'output_dir') and cli_args.output_dir:
            variables["OUTPUT_DIR"] = cli_args.output_dir

        return variables

    def _build_system_hint(self, step: PipelineStep, variables: dict[str, str]) -> str:
        """Build system hint with previous results for context."""
        parts = ["Previous results:"]

        for dep_id in step.depends_on:
            if dep_id in self.completed_summaries:
                parts.append(f"\n{dep_id} result: {self.completed_summaries[dep_id][:200]}...")

        parts.append(f"\nCurrent target: {variables.get('TARGET', 'N/A')}")
        parts.append(f"Current domain: {variables.get('DOMAIN', 'N/A')}")
        return "\n".join(parts)

    def _get_ready_steps(self) -> list[PipelineStep]:
        """Get steps whose dependencies are all completed."""
        return [
            step for step in self.steps.values()
            if step.status == StepStatus.PENDING
            and all(
                dep in self.completed_summaries or dep in self.failed_steps
                for dep in step.depends_on
            )
        ]

    async def _execute_step(self, step: PipelineStep, variables: dict[str, str]) -> None:
        """Execute a single pipeline step with timeout handling."""
        async with self.semaphore:
            step.status = StepStatus.RUNNING
            step.start_time = time.time()

            try:
                prompt = self._apply_variables(step.prompt, variables)
                if step.command and not step.is_report:
                    command = self._apply_variables(step.command, variables)
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

    async def _run_step_worker(self, prompt: str, system_hint: str) -> str:
        """Run a step in a worker process with timeout."""
        from pipeline_runner import PiWorker

        worker = PiWorker(
            model=self.model,
            provider=self.provider,
            timeout=self.step_timeout,
        )
        return worker.run(prompt, system_hint)

    def _apply_variables(self, text: str, variables: dict[str, str]) -> str:
        """Apply variable substitution to text."""
        for key, value in variables.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text

    def _save_step_result(self, step: PipelineStep, output_dir: Path) -> None:
        """Save step result to file."""
        results_dir = output_dir / "summaries"
        results_dir.mkdir(parents=True, exist_ok=True)
        summary_file = results_dir / f"{step.id}.txt"
        summary_file.write_text(step.result, encoding="utf-8")

    def _propagate_failures(self) -> bool:
        """Mark steps with failed deps as failed. Returns True if any were marked."""
        pending = [s for s in self.steps.values() if s.status == StepStatus.PENDING]
        if not pending:
            return False

        made_progress = False
        for step in pending:
            failed_deps = [d for d in step.depends_on if d in self.failed_steps]
            if failed_deps:
                step.status = StepStatus.FAILED
                step.error = f"Skipped — dependencies failed: {', '.join(failed_deps)}"
                self.failed_steps.add(step.id)
                step.end_time = time.time()
                made_progress = True
        return made_progress

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

    async def _generate_report(self, report_step: PipelineStep, variables: dict[str, str]) -> None:
        """Generate and save the final report."""
        print("\nGenerating final report...")
        await self._execute_step(report_step, variables)
        self._save_step_result(report_step, self._output_dir)
        report_file = self._output_dir / "REPORT.md"
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
                    print("Waiting for dependencies to complete...")
                    time.sleep(2)
                continue

            max_concurrent = min(5, len(ready_steps))
            tasks = [self._execute_step(step, variables) for step in ready_steps[:max_concurrent]]

            print(f"Executing {len(tasks)} steps concurrently...")
            await asyncio.gather(*tasks, return_exceptions=True)

            new_done, new_fail = self._tally_progress(counted_steps)
            completed_count += new_done
            failed_count += new_fail

        report_step = self._find_report_step()
        if report_step:
            await self._generate_report(report_step, variables)

        self._print_summary(completed_count, failed_count, output_dir)

        if report_step:
            print("\n" + report_step.result)


def main():
    parser = argparse.ArgumentParser(description="Parallel Pipeline Runner")
    parser.add_argument("pipeline", help="Path to pipeline YAML file")
    parser.add_argument("--target", help="Target domain/IP")
    parser.add_argument("--domain", help="Domain for OSINT")
    parser.add_argument("--model", default="default", help="Model to use")
    parser.add_argument("--provider", default="default", help="Provider to use")
    parser.add_argument("--step-timeout", type=int, default=300, help="Timeout per step in seconds")
    parser.add_argument("--output-dir", help="Output directory")

    args = parser.parse_args()

    if not Path(args.pipeline).exists():
        print(f"Pipeline file not found: {args.pipeline}")
        sys.exit(1)

    runner = ParallelPipelineRunner(
        model=args.model,
        provider=args.provider,
        step_timeout=args.step_timeout,
    )

    asyncio.run(runner.run_pipeline(args.pipeline, args))


if __name__ == "__main__":
    main()
