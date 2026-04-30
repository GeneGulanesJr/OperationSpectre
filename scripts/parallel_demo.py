#!/usr/bin/env python3
"""
Parallel Pipeline Demo - Shows the performance improvement of parallel execution
Usage: python3 scripts/parallel_demo.py
"""

import subprocess
import sys
import time
from pathlib import Path


def run_sequential_pipeline():
    """Run the original sequential pipeline"""
    print("🔄 Running SEQUENTIAL pipeline...")
    start_time = time.time()

    cmd = [
        "python3", "scripts/pipeline_runner.py",
        "scripts/pipelines/parallel_pentest.yaml",
        "--target", "example.com",
        "--domain", "example.com"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        elapsed = time.time() - start_time
        print(f"Sequential execution completed in {elapsed:.1f} seconds")
        return elapsed, result.returncode == 0
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"Sequential execution timed out after {elapsed:.1f} seconds")
        return elapsed, False
    except Exception as e:
        print(f"Sequential execution failed: {e}")
        return 0, False


def run_parallel_pipeline():
    """Run the new parallel pipeline"""
    print("⚡ Running PARALLEL pipeline...")
    start_time = time.time()

    cmd = [
        "python3", "scripts/pipeline_runner.py",
        "scripts/pipelines/parallel_pentest.yaml",
        "--target", "example.com",
        "--domain", "example.com",
        "--parallel"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        elapsed = time.time() - start_time
        print(f"Parallel execution completed in {elapsed:.1f} seconds")
        return elapsed, result.returncode == 0
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"Parallel execution timed out after {elapsed:.1f} seconds")
        return elapsed, False
    except Exception as e:
        print(f"Parallel execution failed: {e}")
        return 0, False


def main():
    print("🚀 OperationSpectre Parallel Execution Demo")
    print("=" * 50)

    # Check if required files exist
    if not Path("scripts/pipeline_runner.py").exists():
        print("❌ pipeline_runner.py not found!")
        sys.exit(1)

    if not Path("scripts/pipelines/parallel_pentest.yaml").exists():
        print("❌ parallel_pentest.yaml not found!")
        sys.exit(1)

    print("📊 Performance Comparison Demo")
    print("This will demonstrate the speed improvement of parallel execution")
    print("(Note: This is a demo - actual improvement depends on network latency and tool performance)")
    print()

    # Run sequential pipeline
    sequential_time, sequential_success = run_sequential_pipeline()
    print()

    # Run parallel pipeline
    parallel_time, parallel_success = run_parallel_pipeline()
    print()

    # Compare results
    print("📈 RESULTS COMPARISON")
    print("=" * 50)
    print(f"Sequential: {sequential_time:.1f}s {'✓' if sequential_success else '✗'}")
    print(f"Parallel:   {parallel_time:.1f}s {'✓' if parallel_success else '✗'}")

    if sequential_time > 0 and parallel_time > 0:
        improvement = ((sequential_time - parallel_time) / sequential_time) * 100
        speedup = sequential_time / parallel_time
        print(f"⚡ Improvement: {improvement:.1f}% faster")
        print(f"🚀 Speedup: {speedup:.1f}x")

        if improvement > 20:
            print("🎉 Significant performance improvement achieved!")
        elif improvement > 0:
            print("👍 Noticeable performance improvement")
        else:
            print("⚠️  No significant improvement (may be limited by network latency)")

    print()
    print("💡 TIPS FOR MAXIMUM PERFORMANCE:")
    print("1. Use --parallel flag for independent scanning tasks")
    print("2. Structure pipelines to maximize parallel opportunities")
    print("3. Adjust --step-timeout based on tool performance")
    print("4. Use appropriate concurrency limits for your system")


if __name__ == "__main__":
    main()
