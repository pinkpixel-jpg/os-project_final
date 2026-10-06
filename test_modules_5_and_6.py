"""
Unit tests for Module 3 (Workload), Module 5 (Metrics), and Module 6 (Display).
Validates that:
- Workloads execute deterministically.
- Metrics collector records accurate execution timing and CPU utilization.
- Repeated runs aggregation computes mean, min, max, and std deviation accurately.
- Display module formats results without encoding errors.
- Export functions output valid CSV and TXT files.

Run with:
    python -m unittest test_modules_5_and_6.py -v
"""

import os
import tempfile
import unittest
from metrics import PerformanceMonitor, RunMetrics, aggregate_runs
from workload import (
    WorkloadType,
    get_workload_function,
    run_crypto_hash_workload,
    run_matrix_mult_workload,
    run_prime_sieve_workload,
)
from display import (
    display_single_run_result,
    display_configuration_summary,
    display_comparison_summary,
    export_results_to_csv,
    export_results_to_txt,
    _render_bar,
)


class TestModule3Workload(unittest.TestCase):
    """Module 3 unit tests."""

    def test_crypto_hash_deterministic(self):
        r1 = run_crypto_hash_workload(0, iterations=50, chunk_size_kb=16)
        r2 = run_crypto_hash_workload(1, iterations=50, chunk_size_kb=16)
        self.assertEqual(r1, 50)
        self.assertEqual(r2, 50)

    def test_matrix_mult_deterministic(self):
        c1 = run_matrix_mult_workload(0, matrix_size=20)
        c2 = run_matrix_mult_workload(1, matrix_size=20)
        self.assertEqual(c1, c2)
        self.assertGreater(c1, 0)

    def test_prime_sieve_deterministic(self):
        p1 = run_prime_sieve_workload(0, limit=1000)
        p2 = run_prime_sieve_workload(1, limit=1000)
        self.assertEqual(p1, 168)
        self.assertEqual(p2, 168)

    def test_get_workload_factory(self):
        func = get_workload_function(WorkloadType.CRYPTO_HASH, intensity=10)
        res = func(0)
        self.assertEqual(res, 10)


class TestModule5Metrics(unittest.TestCase):
    """Module 5 unit tests."""

    def test_performance_monitor_timing(self):
        cores = [0, 1, 2, 3]
        mapping = {0: [0], 1: [1]}
        monitor = PerformanceMonitor(
            "test_config", 2, cores, mapping, run_number=1, sample_interval_sec=0.02
        )
        with monitor:
            import time
            time.sleep(0.08)
        metrics = monitor.metrics
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.execution_time_sec, 0.05)
        self.assertEqual(metrics.thread_count, 2)
        self.assertEqual(metrics.core_count, 4)
        self.assertEqual(metrics.run_number, 1)

    def test_run_metrics_serialization(self):
        rm = RunMetrics(
            config_name="fixed",
            thread_count=2,
            core_count=4,
            thread_to_cores={0: [0], 1: [1]},
            run_number=2,
            logical_cpu_count=4,
            physical_core_count=2,
            execution_time_sec=0.1234,
            system_avg_cpu=25.0,
            active_cores_avg_cpu=50.0,
            timestamp_iso="2026-10-06 12:00:00",
        )
        d = rm.to_dict()
        self.assertEqual(d["config_name"], "fixed")
        self.assertEqual(d["run_number"], 2)
        self.assertEqual(d["thread_count"], 2)

        row = rm.to_csv_row()
        self.assertEqual(row["Configuration"], "FIXED")
        self.assertEqual(row["Run_Number"], 2)
        self.assertEqual(row["Execution_Time_s"], "0.1234")

    def test_aggregate_runs_statistics(self):
        rm1 = RunMetrics(
            config_name="fixed",
            thread_count=2,
            core_count=4,
            thread_to_cores={0: [0], 1: [1]},
            run_number=1,
            execution_time_sec=1.0,
            system_avg_cpu=20.0,
            active_cores_avg_cpu=40.0,
        )
        rm2 = RunMetrics(
            config_name="fixed",
            thread_count=2,
            core_count=4,
            thread_to_cores={0: [0], 1: [1]},
            run_number=2,
            execution_time_sec=2.0,
            system_avg_cpu=30.0,
            active_cores_avg_cpu=60.0,
        )
        summary = aggregate_runs("fixed", [rm1, rm2], physical_core_count=2)
        self.assertEqual(summary.run_count, 2)
        self.assertEqual(summary.avg_time_sec, 1.5)
        self.assertEqual(summary.min_time_sec, 1.0)
        self.assertEqual(summary.max_time_sec, 2.0)
        self.assertAlmostEqual(summary.std_dev_time_sec, 0.707106, places=4)
        self.assertEqual(summary.avg_system_cpu, 25.0)
        self.assertEqual(summary.avg_target_cpu, 50.0)


class TestModule6Display(unittest.TestCase):
    """Module 6 unit tests."""

    def setUp(self):
        self.rm1 = RunMetrics(
            config_name="baseline",
            thread_count=2,
            core_count=4,
            thread_to_cores={0: [], 1: []},
            run_number=1,
            execution_time_sec=1.0,
            avg_per_core_cpu=[20.0, 20.0, 20.0, 20.0],
            system_avg_cpu=20.0,
            active_cores_avg_cpu=20.0,
            timestamp_iso="2026-10-06 12:00:00",
        )
        self.rm2 = RunMetrics(
            config_name="fixed",
            thread_count=2,
            core_count=4,
            thread_to_cores={0: [0], 1: [1]},
            run_number=1,
            execution_time_sec=0.5,
            avg_per_core_cpu=[80.0, 80.0, 2.0, 2.0],
            system_avg_cpu=41.0,
            active_cores_avg_cpu=80.0,
            timestamp_iso="2026-10-06 12:00:05",
        )
        self.sum1 = aggregate_runs("baseline", [self.rm1], physical_core_count=2)
        self.sum2 = aggregate_runs("fixed", [self.rm2], physical_core_count=2)

    def test_render_bar_ascii(self):
        bar = _render_bar(50.0, width=10)
        self.assertIn("#####-----", bar)
        self.assertIn("50.0%", bar)

    def test_display_functions_no_exception(self):
        display_single_run_result(self.rm1)
        display_configuration_summary(self.sum1)
        display_comparison_summary([self.sum1, self.sum2])

    def test_csv_export(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
            path = tf.name
        try:
            export_results_to_csv([self.rm1, self.rm2], filepath=path)
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("BASELINE", content)
            self.assertIn("FIXED", content)
            self.assertIn("Run_Number", content)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_txt_export(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            path = tf.name
        try:
            export_results_to_txt([self.sum1, self.sum2], [self.rm1, self.rm2], filepath=path)
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("PROJECT 31: THREAD AFFINITY MANAGEMENT BENCHMARK REPORT", content)
            self.assertIn("Fastest observed configuration", content)
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()
