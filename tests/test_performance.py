from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from opspectre.config import ConfigError
from opspectre.performance import PerformanceLogger, PerformanceMetrics


@pytest.fixture
def perf_logger():
    with patch.object(ConfigError, "__init__", side_effect=ConfigError):
        pass
    logger = PerformanceLogger()
    logger.enabled = True
    logger.metrics.clear()
    return logger


def _make_metric(
    operation="test_op",
    duration=1.0,
    success=True,
    minutes_ago=0,
):
    return PerformanceMetrics(
        operation=operation,
        duration=duration,
        success=success,
        timestamp=datetime.now() - timedelta(minutes=minutes_ago),
    )


class TestPerformanceLoggerMeasure:
    def test_measure_records_success(self, perf_logger):
        with perf_logger.measure("test_op"):
            pass
        assert len(perf_logger.metrics) == 1
        assert perf_logger.metrics[0].operation == "test_op"
        assert perf_logger.metrics[0].success is True

    def test_measure_records_failure(self, perf_logger):
        with pytest.raises(ValueError):
            with perf_logger.measure("failing_op"):
                raise ValueError("boom")
        assert len(perf_logger.metrics) == 1
        assert perf_logger.metrics[0].success is False

    def test_measure_disabled(self, perf_logger):
        perf_logger.enabled = False
        with perf_logger.measure("disabled_op"):
            pass
        assert len(perf_logger.metrics) == 0

    def test_measure_captures_kwargs(self, perf_logger):
        with perf_logger.measure("op_with_data", key="value"):
            pass
        assert perf_logger.metrics[0].additional_data == {"key": "value"}


class TestGetOperationStats:
    def test_no_metrics(self, perf_logger):
        assert perf_logger.get_operation_stats("nonexistent") == {}

    def test_single_operation(self, perf_logger):
        perf_logger.metrics = [
            _make_metric("scan", duration=2.0, success=True),
            _make_metric("scan", duration=4.0, success=False),
            _make_metric("scan", duration=3.0, success=True),
        ]
        stats = perf_logger.get_operation_stats("scan")
        assert stats["count"] == 3
        assert stats["success_count"] == 2
        assert stats["error_count"] == 1
        assert abs(stats["avg_duration"] - 3.0) < 0.01
        assert stats["min_duration"] == 2.0
        assert stats["max_duration"] == 4.0
        assert abs(stats["success_rate"] - 2 / 3) < 0.01

    def test_only_successes(self, perf_logger):
        perf_logger.metrics = [
            _make_metric("op", duration=1.0, success=True),
        ]
        stats = perf_logger.get_operation_stats("op")
        assert stats["error_count"] == 0
        assert stats["success_rate"] == 1.0


class TestGetAllStats:
    def test_multiple_operations(self, perf_logger):
        perf_logger.metrics = [
            _make_metric("op_a", duration=1.0),
            _make_metric("op_b", duration=2.0),
        ]
        stats = perf_logger.get_all_stats()
        assert "op_a" in stats
        assert "op_b" in stats
        assert stats["op_a"]["count"] == 1
        assert stats["op_b"]["count"] == 1

    def test_empty(self, perf_logger):
        assert perf_logger.get_all_stats() == {}


class TestGetErrorRates:
    def test_no_errors(self, perf_logger):
        perf_logger.metrics = [
            _make_metric("op", success=True),
            _make_metric("op", success=True),
        ]
        rates = perf_logger.get_error_rates()
        assert rates["op"] == 0.0

    def test_mixed(self, perf_logger):
        perf_logger.metrics = [
            _make_metric("op", success=True),
            _make_metric("op", success=False),
        ]
        rates = perf_logger.get_error_rates()
        assert rates["op"] == 0.5


class TestGetBottlenecks:
    def test_no_bottlenecks(self, perf_logger):
        perf_logger.metrics = [_make_metric("op", duration=1.0)]
        assert perf_logger.get_bottlenecks(threshold_seconds=10.0) == []

    def test_finds_bottleneck(self, perf_logger):
        perf_logger.metrics = [
            _make_metric("fast", duration=1.0),
            _make_metric("slow", duration=10.0),
        ]
        bottlenecks = perf_logger.get_bottlenecks(threshold_seconds=5.0)
        assert len(bottlenecks) == 1
        assert bottlenecks[0]["operation"] == "slow"
        assert bottlenecks[0]["duration"] == 10.0

    def test_sorted_by_duration_desc(self, perf_logger):
        perf_logger.metrics = [
            _make_metric("medium", duration=8.0),
            _make_metric("slowest", duration=20.0),
            _make_metric("slower", duration=12.0),
        ]
        bottlenecks = perf_logger.get_bottlenecks(threshold_seconds=5.0)
        assert [b["duration"] for b in bottlenecks] == [20.0, 12.0, 8.0]


class TestClearMetrics:
    def test_clear_all(self, perf_logger):
        perf_logger.metrics = [_make_metric("a"), _make_metric("b")]
        cleared = perf_logger.clear_metrics()
        assert cleared == 2
        assert len(perf_logger.metrics) == 0

    def test_clear_specific_operation(self, perf_logger):
        perf_logger.metrics = [
            _make_metric("keep"),
            _make_metric("remove"),
            _make_metric("keep"),
        ]
        cleared = perf_logger.clear_metrics("remove")
        assert cleared == 1
        assert len(perf_logger.metrics) == 2
        assert all(m.operation == "keep" for m in perf_logger.metrics)


class TestClearOldMetrics:
    def test_removes_old(self, perf_logger):
        perf_logger.metrics = [
            _make_metric("old", minutes_ago=120),
            _make_metric("recent", minutes_ago=5),
        ]
        perf_logger.clear_old_metrics(hours=1)
        assert len(perf_logger.metrics) == 1
        assert perf_logger.metrics[0].operation == "recent"

    def test_keeps_all_recent(self, perf_logger):
        perf_logger.metrics = [_make_metric("a", minutes_ago=5)]
        perf_logger.clear_old_metrics(hours=1)
        assert len(perf_logger.metrics) == 1


class TestExportMetrics:
    def test_json_export(self, perf_logger):
        perf_logger.metrics = [_make_metric("op", duration=1.5)]
        exported = perf_logger.export_metrics("json")
        import json
        data = json.loads(exported)
        assert "export_time" in data
        assert data["total_metrics"] == 1
        assert "op" in data["operations"]

    def test_csv_export(self, perf_logger):
        perf_logger.metrics = [_make_metric("op")]
        exported = perf_logger.export_metrics("csv")
        assert "operation" in exported
        assert "op" in exported

    def test_unsupported_format(self, perf_logger):
        with pytest.raises(ValueError, match="Unsupported format"):
            perf_logger.export_metrics("xml")


class TestAutoPrune:
    def test_prunes_at_cap(self, perf_logger):
        perf_logger.MAX_METRICS = 10
        for i in range(15):
            perf_logger.metrics.append(_make_metric(f"op_{i}"))
        with perf_logger.measure("overflow"):
            pass
        assert len(perf_logger.metrics) <= perf_logger.MAX_METRICS
