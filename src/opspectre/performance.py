import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .config import Config, ConfigError


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation."""
    operation: str
    duration: float
    success: bool
    timestamp: datetime
    additional_data: dict[str, Any] = field(default_factory=dict)


class PerformanceLogger:
    """Performance monitoring and analytics for OperationSpectre."""

    MAX_METRICS = 1000  # Hard cap to prevent unbounded memory growth

    def __init__(self):
        # Performance logging is enabled by default for intentional monitoring
        try:
            self.enabled = Config.get_bool("opspectre_performance_logging")
        except ConfigError:
            # Fallback: always enabled for intentional monitoring
            self.enabled = True
        self.metrics: list[PerformanceMetrics] = []
        self._lock = threading.Lock()
        self.logger = logging.getLogger("opspectre.performance")
        self._slow_threshold_s: float | None = None  # cached in seconds

        # Configure logger
        if self.enabled and not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] [PERFORMANCE] %(message)s",
                datefmt="%H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    @contextmanager
    def measure(self, operation: str, **kwargs):
        """Measure execution time of an operation."""
        if not self.enabled:
            yield
            return

        start_time = time.perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.perf_counter() - start_time
            metric = PerformanceMetrics(
                operation=operation,
                duration=duration,
                success=success,
                timestamp=datetime.now(),
                additional_data=kwargs
            )
            with self._lock:
                self.metrics.append(metric)
            self._log_metric(metric)

    def _get_slow_threshold(self) -> float:
        """Return the slow-operation threshold in seconds (cached)."""
        if self._slow_threshold_s is None:
            try:
                threshold_ms = Config.get_int("opspectre_slow_operation_threshold")
                self._slow_threshold_s = threshold_ms / 1000.0
            except ConfigError:
                self._slow_threshold_s = 5.0
        return self._slow_threshold_s

    def _log_metric(self, metric: PerformanceMetrics):
        """Log a performance metric."""
        slow_threshold = self._get_slow_threshold()

        if not metric.success:
            self.logger.error(
                f"{metric.operation} failed in {metric.duration:.2f}s "
                f"{metric.additional_data}"
            )
        elif metric.duration > slow_threshold:
            self.logger.warning(
                f"{metric.operation} took {metric.duration:.2f}s "
                f"{metric.additional_data}"
            )
        else:
            self.logger.info(
                f"{metric.operation} completed in {metric.duration:.2f}s "
                f"{metric.additional_data}"
            )

        # Auto-prune if metrics list exceeds cap — drop oldest entries
        with self._lock:
            if len(self.metrics) > self.MAX_METRICS:
                self.metrics = self.metrics[-(self.MAX_METRICS // 2):]

    def get_operation_stats(self, operation: str) -> dict[str, Any]:
        """Get statistics for a specific operation."""
        with self._lock:
            op_metrics = [m for m in self.metrics if m.operation == operation]
        if not op_metrics:
            return {}

        durations = [m.duration for m in op_metrics]
        success_count = sum(1 for m in op_metrics if m.success)
        error_count = len(op_metrics) - success_count

        # Calculate time span for error rate
        timestamps = [m.timestamp.timestamp() for m in op_metrics]
        time_span = (max(timestamps) - min(timestamps)) or 1
        errors_per_minute = (error_count / time_span) * 60 if op_metrics else 0

        return {
            "count": len(op_metrics),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_count / len(op_metrics) if op_metrics else 0,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_duration": sum(durations),
            "errors_per_minute": errors_per_minute,
        }

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all operations."""
        with self._lock:
            all_operations = set(m.operation for m in self.metrics)
        return {op: self.get_operation_stats(op) for op in all_operations}

    def get_error_rates(self) -> dict[str, float]:
        """Calculate error rates per operation type."""
        error_rates = {}
        with self._lock:
            operations = set(m.operation for m in self.metrics)
            for operation in operations:
                op_metrics = [m for m in self.metrics if m.operation == operation]
                errors = sum(1 for m in op_metrics if not m.success)
                error_rates[operation] = errors / len(op_metrics) if op_metrics else 0
        return error_rates

    def get_bottlenecks(self, threshold_seconds: float = 5.0) -> list[dict[str, Any]]:
        """Find operations that are slower than threshold."""
        with self._lock:
            slow_ops = [
                {
                    "operation": metric.operation,
                    "duration": metric.duration,
                    "timestamp": metric.timestamp,
                    "success": metric.success,
                    "data": metric.additional_data
                }
                for metric in self.metrics
                if metric.duration > threshold_seconds
            ]
        return sorted(slow_ops, key=lambda x: x["duration"], reverse=True)

    def clear_old_metrics(self, hours: int = 24):
        """Clear metrics older than specified hours."""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        with self._lock:
            self.metrics = [m for m in self.metrics if m.timestamp.timestamp() > cutoff_time]

    def clear_metrics(self, operation: str | None = None) -> int:
        """Clear metrics, optionally for a specific operation."""
        with self._lock:
            if operation:
                original_count = len(self.metrics)
                self.metrics = [m for m in self.metrics if m.operation != operation]
                return original_count - len(self.metrics)
            else:
                original_count = len(self.metrics)
                self.metrics.clear()
                return original_count

    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format."""
        with self._lock:
            metrics_snapshot = list(self.metrics)
        if format_type == "json":
            import json
            data = {
                "export_time": datetime.now().isoformat(),
                "total_metrics": len(metrics_snapshot),
                "operations": self.get_all_stats()
            }
            return json.dumps(data, indent=2, default=str)
        elif format_type == "csv":
            import csv
            from io import StringIO
            output = StringIO()
            fieldnames = ["operation", "duration", "success", "timestamp", "additional_data"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for metric in metrics_snapshot:
                writer.writerow({
                    "operation": metric.operation,
                    "duration": metric.duration,
                    "success": metric.success,
                    "timestamp": metric.timestamp.isoformat(),
                    "additional_data": str(metric.additional_data)
                })
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format_type}")


# Global performance logger instance
performance_logger = PerformanceLogger()
