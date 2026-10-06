"""
Module 5: Performance Measurement
Project: Thread Affinity Management for Multi-Core Processors (Phase 1)

This module handles:
1. High-precision wall-clock timing using time.perf_counter().
2. Tracking active thread counts, logical processor counts, physical core counts,
   and thread-to-core assignment metadata.
3. Background sampling of per-core CPU utilization via psutil.cpu_percent(percpu=True).
4. Generating structured RunMetrics objects for individual runs.
5. Statistical aggregation across multiple repeated benchmark runs
   (mean, min, max, standard deviation, and average CPU utilization).
"""

from __future__ import annotations

import datetime
import math
import statistics
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class RunMetrics:
    """
    Structured performance metrics for a single execution run.
    """
    config_name: str
    thread_count: int
    core_count: int
    thread_to_cores: Dict[int, List[int]]
    run_number: int = 1
    logical_cpu_count: int = 0
    physical_core_count: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    execution_time_sec: float = 0.0
    per_core_samples: List[List[float]] = field(default_factory=list)
    avg_per_core_cpu: List[float] = field(default_factory=list)
    peak_per_core_cpu: List[float] = field(default_factory=list)
    system_avg_cpu: float = 0.0
    active_cores_avg_cpu: float = 0.0
    timestamp_iso: str = ""
    thread_statuses: Dict[int, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serializes the metrics to a standard dictionary."""
        return {
            "config_name": self.config_name,
            "run_number": self.run_number,
            "thread_count": self.thread_count,
            "logical_cpu_count": self.logical_cpu_count or self.core_count,
            "physical_core_count": self.physical_core_count,
            "thread_to_cores": {str(k): v for k, v in self.thread_to_cores.items()},
            "execution_time_sec": round(self.execution_time_sec, 4),
            "system_avg_cpu": round(self.system_avg_cpu, 2),
            "active_cores_avg_cpu": round(self.active_cores_avg_cpu, 2),
            "avg_per_core_cpu": [round(val, 2) for val in self.avg_per_core_cpu],
            "peak_per_core_cpu": [round(val, 2) for val in self.peak_per_core_cpu],
            "timestamp_iso": self.timestamp_iso,
        }

    def to_csv_row(self) -> dict:
        """Returns flattened dictionary suitable for CSV export."""
        assigned_str = ";".join(
            f"T{t}->{','.join(str(c) for c in cores) if cores else 'OS'}"
            for t, cores in sorted(self.thread_to_cores.items())
        )
        return {
            "Timestamp": self.timestamp_iso,
            "Configuration": self.config_name.upper(),
            "Run_Number": self.run_number,
            "Thread_Count": self.thread_count,
            "Logical_Processors": self.logical_cpu_count or self.core_count,
            "Physical_Cores": self.physical_core_count,
            "Assignments": assigned_str,
            "Execution_Time_s": f"{self.execution_time_sec:.4f}",
            "System_Avg_CPU_pct": f"{self.system_avg_cpu:.2f}",
            "Target_Cores_Avg_CPU_pct": f"{self.active_cores_avg_cpu:.2f}",
        }


@dataclass
class ConfigurationSummary:
    """
    Statistical summary aggregated across multiple repeated runs of a configuration.
    """
    config_name: str
    thread_count: int
    logical_cpu_count: int
    physical_core_count: int
    run_count: int
    avg_time_sec: float
    min_time_sec: float
    max_time_sec: float
    std_dev_time_sec: float
    avg_system_cpu: float
    avg_target_cpu: float
    runs: List[RunMetrics] = field(default_factory=list)
    thread_to_cores: Dict[int, List[int]] = field(default_factory=dict)
    representative_run: Optional[RunMetrics] = None

    def speedup_vs(self, baseline_summary: ConfigurationSummary) -> float:
        """
        Calculates speedup ratio relative to baseline average execution time:
            speedup = baseline_avg_time / configuration_avg_time
        """
        if self.avg_time_sec > 0:
            return baseline_summary.avg_time_sec / self.avg_time_sec
        return 1.0


def aggregate_runs(
    config_name: str,
    runs: List[RunMetrics],
    physical_core_count: int = 0,
) -> ConfigurationSummary:
    """
    Aggregates multiple RunMetrics into a single ConfigurationSummary.
    """
    if not runs:
        raise ValueError("Cannot aggregate empty list of runs.")

    times = [r.execution_time_sec for r in runs]
    sys_cpus = [r.system_avg_cpu for r in runs]
    target_cpus = [r.active_cores_avg_cpu for r in runs]

    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0.0

    avg_sys = statistics.mean(sys_cpus) if sys_cpus else 0.0
    avg_target = statistics.mean(target_cpus) if target_cpus else 0.0

    first = runs[0]
    return ConfigurationSummary(
        config_name=config_name,
        thread_count=first.thread_count,
        logical_cpu_count=first.logical_cpu_count or first.core_count,
        physical_core_count=physical_core_count or first.physical_core_count,
        run_count=len(runs),
        avg_time_sec=avg_time,
        min_time_sec=min_time,
        max_time_sec=max_time,
        std_dev_time_sec=std_dev,
        avg_system_cpu=avg_sys,
        avg_target_cpu=avg_target,
        runs=runs,
        thread_to_cores=first.thread_to_cores,
        representative_run=runs[-1],
    )


class CpuUtilizationSampler(threading.Thread):
    """
    Background sampling thread that collects periodic per-core CPU utilization
    metrics without disturbing worker threads.
    """

    def __init__(self, sample_interval_sec: float = 0.08):
        super().__init__(daemon=True, name="CPUMonitorThread")
        self.sample_interval_sec = sample_interval_sec
        self._stop_event = threading.Event()
        self.samples: List[List[float]] = []

    def run(self) -> None:
        if not PSUTIL_AVAILABLE:
            return

        psutil.cpu_percent(percpu=True)
        while not self._stop_event.is_set():
            time.sleep(self.sample_interval_sec)
            if self._stop_event.is_set():
                break
            try:
                per_cpu = psutil.cpu_percent(percpu=True)
                if per_cpu:
                    self.samples.append(per_cpu)
            except Exception:
                pass

    def stop(self) -> List[List[float]]:
        """Stops the sampling thread and returns collected samples."""
        self._stop_event.set()
        self.join(timeout=1.0)
        return self.samples


class PerformanceMonitor:
    """
    Context manager for measuring execution time and per-core CPU metrics.
    """

    def __init__(
        self,
        config_name: str,
        thread_count: int,
        available_core_ids: List[int],
        thread_to_cores: Dict[int, List[int]],
        run_number: int = 1,
        physical_core_count: int = 0,
        sample_interval_sec: float = 0.08,
    ):
        self.config_name = config_name
        self.thread_count = thread_count
        self.available_core_ids = available_core_ids
        self.thread_to_cores = thread_to_cores
        self.run_number = run_number
        self.physical_core_count = physical_core_count
        self.sample_interval_sec = sample_interval_sec
        self.metrics: Optional[RunMetrics] = None

        self._start_perf: float = 0.0
        self._end_perf: float = 0.0
        self._sampler: Optional[CpuUtilizationSampler] = None

    def start(self) -> None:
        """Starts timing and CPU utilization monitoring."""
        self.metrics = None
        self._sampler = CpuUtilizationSampler(self.sample_interval_sec)
        self._sampler.start()
        self._start_perf = time.perf_counter()

    def stop(self, thread_statuses: Optional[Dict[int, str]] = None) -> RunMetrics:
        """
        Stops monitoring, calculates metrics, and stores the completed RunMetrics.
        """
        self._end_perf = time.perf_counter()
        raw_samples = self._sampler.stop() if self._sampler else []

        duration = max(0.0001, self._end_perf - self._start_perf)
        num_cores = len(self.available_core_ids)

        avg_per_core = [0.0] * num_cores
        peak_per_core = [0.0] * num_cores

        if raw_samples:
            for core_idx in range(num_cores):
                core_vals = [s[core_idx] for s in raw_samples if core_idx < len(s)]
                if core_vals:
                    avg_per_core[core_idx] = sum(core_vals) / len(core_vals)
                    peak_per_core[core_idx] = max(core_vals)

        if any(avg_per_core):
            system_avg = sum(avg_per_core) / len(avg_per_core)
        else:
            system_avg = 0.0

        assigned_cores_set = set()
        for cores in self.thread_to_cores.values():
            assigned_cores_set.update(cores)

        if assigned_cores_set:
            active_vals = [avg_per_core[c] for c in assigned_cores_set if c < len(avg_per_core)]
            active_avg = sum(active_vals) / len(active_vals) if active_vals else system_avg
        else:
            active_avg = system_avg

        self.metrics = RunMetrics(
            config_name=self.config_name,
            thread_count=self.thread_count,
            core_count=num_cores,
            thread_to_cores=self.thread_to_cores,
            run_number=self.run_number,
            logical_cpu_count=num_cores,
            physical_core_count=self.physical_core_count,
            start_time=self._start_perf,
            end_time=self._end_perf,
            execution_time_sec=duration,
            per_core_samples=raw_samples,
            avg_per_core_cpu=avg_per_core,
            peak_per_core_cpu=peak_per_core,
            system_avg_cpu=system_avg,
            active_cores_avg_cpu=active_avg,
            timestamp_iso=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            thread_statuses=thread_statuses or {},
        )
        return self.metrics

    def __enter__(self) -> PerformanceMonitor:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.metrics is None:
            self.stop()


if __name__ == "__main__":
    print("Testing Module 5: Performance Measurement standalone...")
    dummy_mapping = {0: [0], 1: [1]}
    cores = [0, 1, 2, 3]

    monitor = PerformanceMonitor("test_config", 2, cores, dummy_mapping, run_number=1, physical_core_count=2)
    with monitor:
        time.sleep(0.1)
    res = monitor.metrics
    print(f"  [+] Single run: time={res.execution_time_sec:.4f}s, sys_cpu={res.system_avg_cpu:.1f}%")

    summary = aggregate_runs("test_config", [res, res], physical_core_count=2)
    print(f"  [+] Aggregated summary: avg_time={summary.avg_time_sec:.4f}s, runs={summary.run_count}")
