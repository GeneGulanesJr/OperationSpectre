"""Performance analytics and monitoring commands."""

import argparse
import os
from typing import Any

from opspectre.config import Config, ConfigError
from opspectre.performance import performance_logger

# Success rate thresholds for color coding
SUCCESS_RATE_GREEN = 0.95
SUCCESS_RATE_YELLOW = 0.80

# Display limits
BOTTLENECK_DISPLAY_LIMIT = 10
DASH_LINE_WIDTH = 80
ERROR_DASH_WIDTH = 30
BOTTLENECK_DASH_WIDTH = 50


def _color_for_rate(rate: float) -> str:
    """Return a rich color tag based on success rate threshold."""
    if rate >= SUCCESS_RATE_GREEN:
        return "[green]"
    if rate >= SUCCESS_RATE_YELLOW:
        return "[yellow]"
    return "[red]"


def _print_overview_table(console: Any, all_stats: dict) -> None:
    """Print the main performance stats table."""
    console.print("[bold]Performance Overview:[/]")
    console.print("Operation\tCount\tSuccess Rate\tAvg Duration\tMax Duration")
    console.print("-" * DASH_LINE_WIDTH)

    for operation, stats in all_stats.items():
        success_rate = f"{stats['success_rate']:.1%}"
        avg_duration = f"{stats['avg_duration']:.2f}s"
        max_duration = f"{stats['max_duration']:.2f}s"
        color = _color_for_rate(stats["success_rate"])
        console.print(
            f"{operation}\t{stats['count']}\t{color}{success_rate}[/]\t"
            f"{avg_duration}\t{max_duration}"
        )


def _print_error_rates(console: Any, error_rates: dict) -> None:
    """Print error rates section if any errors exist."""
    error_ops = {op: rate for op, rate in error_rates.items() if rate > 0}
    if not error_ops:
        return
    console.print()
    console.print("[bold]Error Rates:[/]")
    console.print("Operation\tError Rate")
    console.print("-" * ERROR_DASH_WIDTH)
    for operation, rate in error_ops.items():
        console.print(f"{operation}\t{rate:.1%}")


def _print_bottlenecks(console: Any, bottlenecks: list) -> None:
    """Print slow operations section if any exist."""
    if not bottlenecks:
        return
    console.print()
    console.print("[bold]Performance Bottlenecks (>5s):[/]")
    console.print("Operation\tDuration\tSuccess\tTimestamp")
    console.print("-" * BOTTLENECK_DASH_WIDTH)
    for entry in bottlenecks[:BOTTLENECK_DISPLAY_LIMIT]:
        success_text = "✓" if entry["success"] else "✗"
        timestamp = entry["timestamp"].strftime("%H:%M:%S")
        console.print(
            f"{entry['operation']}\t{entry['duration']:.2f}s\t"
            f"{success_text}\t{timestamp}"
        )


def _print_config_info(console: Any) -> None:
    """Print performance monitoring configuration."""
    console.print()
    console.print("[bold]Configuration:[/]")
    console.print("Performance Logging: Always Enabled (Intentional Monitoring)")
    threshold = Config.get_int("opspectre_slow_operation_threshold")
    console.print(f"Slow Operation Threshold: {threshold}ms")
    console.print(f"Metrics Interval: {Config.get_int('opspectre_metrics_interval')}s")
    console.print(f"Total Metrics Collected: {len(performance_logger.metrics)}")
    console.print("Note: Performance tracking is integrated into all operations by default.")


def _handle_export(console: Any, export_format: str) -> None:
    """Handle --export json|csv."""
    try:
        data = performance_logger.export_metrics(export_format)
        label = export_format.upper()
        console.print(f"\n[bold]{label} Export:[/]")
        console.print(data)
    except Exception as e:
        console.print(f"[red]Error exporting data: {e}[/]")


def cmd_performance(args: argparse.Namespace, console: Any) -> None:
    """Show performance analytics and statistics."""
    console.print("[bold]OperationSpectre Performance Analytics[/]")
    console.print("Performance monitoring is always active during operation.")

    # Clear old metrics (keep last 24 hours)
    performance_logger.clear_old_metrics()

    all_stats = performance_logger.get_all_stats()
    if not all_stats:
        console.print("[dim]No performance data available. Run some operations first.[/]")
        return

    _print_overview_table(console, all_stats)
    _print_error_rates(console, performance_logger.get_error_rates())
    _print_bottlenecks(console, performance_logger.get_bottlenecks())
    _print_config_info(console)

    console.print()
    console.print("[bold]Export Options:[/]")
    console.print("  • Export to JSON: opspectre performance --export json")
    console.print("  • Export to CSV: opspectre performance --export csv")

    if args.export:
        _handle_export(console, args.export)


def cmd_performance_config(args: argparse.Namespace, console: Any) -> None:
    """Configure performance monitoring settings."""
    if args.set:
        _set_config(console, args.set, args.value)
    elif args.get:
        _get_config(console, args.get)
    else:
        _show_config(console)


def _set_config(console: Any, key: str, value: str) -> None:
    """Set a performance config value with validation."""
    if key not in Config._SCHEMA:
        console.print(f"Unknown config key: {key!r}")
        console.print(f"Valid keys: {', '.join(Config._SCHEMA.keys())}")
        return

    env_name = key.upper()
    prev = os.environ.pop(env_name, None)
    os.environ[env_name] = value

    try:
        schema_type = Config._SCHEMA[key][0]
        Config._typed_get(key, schema_type)
    except ConfigError as e:
        if prev is not None:
            os.environ[env_name] = prev
        else:
            os.environ.pop(env_name, None)
        console.print(f"[red]{e}[/]")
        return

    Config.save_current()
    console.print(f"[green]Set {key} = {value}[/]")


def _get_config(console: Any, key: str) -> None:
    """Get and display a performance config value."""
    try:
        value = Config.get(key)
        console.print(f"{key} = {value}")
    except ConfigError:
        console.print(f"Unknown config key: {key}")


def _show_config(console: Any) -> None:
    """Show current performance configuration."""
    console.print("Current Performance Configuration:")
    config_items = [
        "opspectre_performance_logging",
        "opspectre_metrics_interval",
        "opspectre_slow_operation_threshold",
    ]
    for item in config_items:
        try:
            value = Config.get(item)
            console.print(f"  {item} = {value}")
        except ConfigError:
            console.print(f"  {item} = not set")


def cmd_performance_clear(args: argparse.Namespace, console: Any) -> None:
    """Clear performance metrics."""
    if args.operation:
        cleared_count = performance_logger.clear_metrics(args.operation)
        console.print(f"Cleared {cleared_count} metrics for '{args.operation}'")
    else:
        cleared_count = performance_logger.clear_metrics()
        console.print(f"Cleared all {cleared_count} performance metrics")
