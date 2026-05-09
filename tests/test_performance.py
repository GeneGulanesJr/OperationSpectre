import json
import threading
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from opspectre.performance import PerformanceLogger, PerformanceMetrics


@pytest.fixture
def perf_logger():
    with patch("opspectre.performance.Config.get_bool", return_value=True):
        logger = PerformanceLogger()
    logger.metrics.clear()
    return logger


class TestMeasureContextManager:
    def test_records_success_with_duration(self, perf_logger):
        with perf_logger.measure("test_op"):
            pass
        assert len(perf_logger.metrics) == 1
        m = perf_logger.metrics[0]
        assert m.operation == "test_op"
        assert m.success is True
        assert m.duration >= 0

    def test_records_failure_on_exception(self, perf_logger):
        with pytest.raises(ValueError):
            with perf_logger.measure("failing_op"):
                raise ValueError("boom")
        assert len(perf_logger.metrics) == 1
        assert perf_logger.metrics[0].success is False

    def test_records_additional_kwargs(self, perf_logger):
        with perf_logger.measure("op_with_data", target="10.0.0.1", ports="80"):
            pass
        assert perf_logger.metrics[0].additional_data == {"target": "10.0.0.1", "ports": "80"}

    def test_disabled_skips_recording(self, perf_logger):
        perf_logger.enabled = False
        with perf_logger.measure("disabled_op"):
            pass
        assert len(perf_logger.metrics) == 0

    def test_exception_propagates(self, perf_logger):
        with pytest.raises(TypeError, match="bad type"):
            with perf_logger.measure("crash_op"):
                raise TypeError("bad type")

    def test_nested_measures(self, perf_logger):
        with perf_logger.measure("outer"):
            with perf_logger.measure("inner"):
                pass
        assert len(perf_logger.metrics) == 2
        assert perf_logger.metrics[0].operation == "inner"
        assert perf_logger.metrics[1].operation == "outer"

    def test_concurrent_measures(self, perf_logger):
        errors = []

        def measure_op(name):
            try:
                with perf_logger.measure(name):
                    pass
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=measure_op, args=(f"op_{i}",)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(perf_logger.metrics) == 20


class TestGetOperationStatsViaMeasure:
    def test_computes_stats_from_measured_ops(self, perf_logger):
        for _ in range(3):
            with perf_logger.measure("scan"):
                pass
        with pytest.raises(RuntimeError):
            with perf_logger.measure("scan"):
                raise RuntimeError("fail")

        stats = perf_logger.get_operation_stats("scan")
        assert stats["count"] == 4
        assert stats["success_count"] == 3
        assert stats["error_count"] == 1
        assert abs(stats["success_rate"] - 0.75) < 0.01
        assert stats["min_duration"] >= 0
        assert stats["max_duration"] >= stats["min_duration"]

    def test_unknown_operation_returns_empty(self, perf_logger):
        assert perf_logger.get_operation_stats("nonexistent") == {}


class TestGetAllStatsViaMeasure:
    def test_multiple_operations(self, perf_logger):
        with perf_logger.measure("op_a"):
            pass
        with perf_logger.measure("op_b"):
            pass
        stats = perf_logger.get_all_stats()
        assert "op_a" in stats
        assert "op_b" in stats
        assert stats["op_a"]["count"] == 1
        assert stats["op_b"]["count"] == 1


class TestGetErrorRatesViaMeasure:
    def test_mixed(self, perf_logger):
        with perf_logger.measure("op"):
            pass
        with perf_logger.measure("op"):
            pass
        with pytest.raises(Exception):
            with perf_logger.measure("op"):
                raise Exception("fail")
        rates = perf_logger.get_error_rates()
        assert abs(rates["op"] - 1 / 3) < 0.01


class TestGetBottlenecks:
    def test_below_threshold(self, perf_logger):
        with perf_logger.measure("fast"):
            pass
        assert perf_logger.get_bottlenecks(threshold_seconds=10.0) == []

    def test_above_threshold(self, perf_logger):
        with patch("time.perf_counter", side_effect=[0.0, 20.0]):
            with perf_logger.measure("slow"):
                pass
        bottlenecks = perf_logger.get_bottlenecks(threshold_seconds=5.0)
        assert len(bottlenecks) == 1
        assert bottlenecks[0]["operation"] == "slow"
        assert bottlenecks[0]["duration"] == 20.0

    def test_sorted_descending(self, perf_logger):
        with patch("time.perf_counter", side_effect=[0.0, 15.0]):
            with perf_logger.measure("medium"):
                pass
        with patch("time.perf_counter", side_effect=[0.0, 25.0]):
            with perf_logger.measure("slowest"):
                pass
        bottlenecks = perf_logger.get_bottlenecks(threshold_seconds=5.0)
        assert [b["duration"] for b in bottlenecks] == [25.0, 15.0]


class TestClearMetrics:
    def test_clear_all(self, perf_logger):
        with perf_logger.measure("a"):
            pass
        with perf_logger.measure("b"):
            pass
        cleared = perf_logger.clear_metrics()
        assert cleared == 2
        assert len(perf_logger.metrics) == 0

    def test_clear_specific_operation(self, perf_logger):
        with perf_logger.measure("keep"):
            pass
        with perf_logger.measure("remove"):
            pass
        with perf_logger.measure("keep"):
            pass
        cleared = perf_logger.clear_metrics("remove")
        assert cleared == 1
        assert len(perf_logger.metrics) == 2
        assert all(m.operation == "keep" for m in perf_logger.metrics)


class TestClearOldMetrics:
    def test_removes_old(self, perf_logger):
        old = PerformanceMetrics(
            operation="old", duration=1.0, success=True,
            timestamp=datetime.now() - timedelta(hours=120),
        )
        recent = PerformanceMetrics(
            operation="recent", duration=1.0, success=True,
            timestamp=datetime.now() - timedelta(minutes=5),
        )
        perf_logger.metrics.extend([old, recent])
        perf_logger.clear_old_metrics(hours=1)
        assert len(perf_logger.metrics) == 1
        assert perf_logger.metrics[0].operation == "recent"


class TestExportMetrics:
    def test_json_export(self, perf_logger):
        with perf_logger.measure("op"):
            pass
        exported = perf_logger.export_metrics("json")
        data = json.loads(exported)
        assert "export_time" in data
        assert data["total_metrics"] == 1
        assert "op" in data["operations"]

    def test_csv_export(self, perf_logger):
        with perf_logger.measure("op"):
            pass
        exported = perf_logger.export_metrics("csv")
        assert "operation" in exported
        assert "op" in exported

    def test_unsupported_format(self, perf_logger):
        with pytest.raises(ValueError, match="Unsupported format"):
            perf_logger.export_metrics("xml")


class TestAutoPruneViaMeasure:
    def test_prunes_at_cap(self, perf_logger):
        perf_logger.MAX_METRICS = 10
        for i in range(11):
            with perf_logger.measure(f"op_{i}"):
                pass
        assert len(perf_logger.metrics) <= perf_logger.MAX_METRICS
