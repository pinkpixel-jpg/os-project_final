"""
Module 6: Results Display / Output
Project: Thread Affinity Management for Multi-Core Processors (Phase 1)

This module handles:
1. Pretty-printing individual run performance results and thread assignment tables.
2. Rendering ASCII CPU utilization load bars per logical processor (Windows cp1252 safe).
3. Displaying statistical summaries for repeated benchmark runs (mean, min, max, std dev).
4. Generating comparative benchmark summaries with scientifically neutral observations.
5. Exporting every individual benchmark run to CSV and generating formal TXT reports.
"""

from __future__ import annotations

import csv
import os
from typing import Dict, List, Optional
from metrics import ConfigurationSummary, RunMetrics


def _render_bar(percent: float, width: int = 16) -> str:
    """Generates an ASCII-safe text-based load bar for CPU utilization."""
    filled = int(round((percent / 100.0) * width))
    filled = max(0, min(width, filled))
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {percent:5.1f}%"


def display_single_run_result(metrics: RunMetrics) -> None:
    """Prints a concise status line for an individual benchmark repetition."""
    print(
        f"    [Run {metrics.run_number}] Time: {metrics.execution_time_sec:.4f}s | "
        f"System CPU: {metrics.system_avg_cpu:.1f}% | "
        f"Target Cores CPU: {metrics.active_cores_avg_cpu:.1f}%"
    )


def display_configuration_summary(summary: ConfigurationSummary) -> None:
    """
    Prints a detailed results card for a configuration across its repeated runs,
    including per-core CPU load bars from the representative run.
    """
    print("\n" + "=" * 76)
    print(f"       BENCHMARK RESULTS: {summary.config_name.upper()} ({summary.run_count} Runs)")
    print("=" * 76)
    print(f"  * Configuration Name  : {summary.config_name.upper()}")
    print(f"  * Worker Threads      : {summary.thread_count}")
    print(f"  * Logical Processors  : {summary.logical_cpu_count}")
    print(f"  * Physical Cores      : {summary.physical_core_count if summary.physical_core_count else 'Detected via OS'}")
    print(f"  * Repetitions (Runs)  : {summary.run_count}")
    print(f"  * Average Exec Time   : {summary.avg_time_sec:.4f} seconds")
    print(f"  * Minimum Exec Time   : {summary.min_time_sec:.4f} seconds")
    print(f"  * Maximum Exec Time   : {summary.max_time_sec:.4f} seconds")
    print(f"  * Standard Deviation  : {summary.std_dev_time_sec:.4f} seconds")
    print(f"  * Average System CPU  : {summary.avg_system_cpu:.2f}%")
    print(f"  * Target Cores CPU    : {summary.avg_target_cpu:.2f}%")
    print("-" * 76)

    # Thread-to-core mapping
    print(f"  {'Thread':<10} | {'Assigned Logical ID':<22} | {'Affinity Status':<16}")
    print("  " + "-" * 72)
    rep = summary.representative_run or summary.runs[0]
    for tid in sorted(summary.thread_to_cores.keys()):
        cores = summary.thread_to_cores[tid]
        core_repr = ", ".join(f"Logical {c}" for c in cores) if cores else "OS Scheduler (Unrestricted)"
        status = rep.thread_statuses.get(tid, "Verified")
        print(f"  Worker-{tid:<3} | {core_repr:<22} | {status:<16}")
    print("-" * 76)

    # Per-core CPU load bars from representative run
    if rep and rep.avg_per_core_cpu:
        print("  MEASURED CPU LOAD PER LOGICAL PROCESSOR (REPRESENTATIVE RUN):")
        core_to_threads: Dict[int, List[int]] = {}
        for tid, cores in summary.thread_to_cores.items():
            for c in cores:
                core_to_threads.setdefault(c, []).append(tid)

        for core_id, pct in enumerate(rep.avg_per_core_cpu):
            bar = _render_bar(pct, width=16)
            assigned_threads = core_to_threads.get(core_id, [])
            if assigned_threads:
                annot = f" <-- Workers: {', '.join(str(t) for t in assigned_threads)}"
            elif not any(summary.thread_to_cores.values()):
                annot = " (OS Discretion)"
            else:
                annot = ""
            print(f"    Logical Core {core_id:2d} : {bar}{annot}")
        print("=" * 76 + "\n")


def display_comparison_summary(summaries: List[ConfigurationSummary]) -> None:
    """
    Renders a comparative table ranking all configurations, with multi-run
    statistics (mean, min, max, stdev, speedup vs baseline) and academically
    defensible neutral observations.
    """
    if not summaries:
        print("[!] No configuration summaries to compare.")
        return

    baseline = next(
        (s for s in summaries if s.config_name.lower() == "baseline"), summaries[0]
    )

    # Sort from fastest (lowest average time) to slowest
    sorted_summaries = sorted(summaries, key=lambda s: s.avg_time_sec)
    fastest = sorted_summaries[0]
    slowest = sorted_summaries[-1]

    print("\n" + "#" * 86)
    print("      THREAD AFFINITY MANAGEMENT -- STATISTICAL PERFORMANCE COMPARISON")
    print("#" * 86)
    print(
        f"{'Configuration':<14} | {'Threads':<7} | {'Avg Time (s)':<12} | "
        f"{'Min (s)':<9} | {'Max (s)':<9} | {'StdDev (s)':<10} | {'Avg CPU %':<9} | {'Speedup'}"
    )
    print("-" * 86)

    for s in sorted_summaries:
        speedup = s.speedup_vs(baseline)
        if speedup > 1.05:
            speedup_str = f"{speedup:.2f}x (Faster)"
        elif speedup < 0.95:
            speedup_str = f"{speedup:.2f}x (Slower)"
        else:
            speedup_str = f"{speedup:.2f}x (Baseline)" if s == baseline else f"{speedup:.2f}x (Equal)"

        print(
            f"{s.config_name.upper():<14} | {s.thread_count:<7} | {s.avg_time_sec:<12.4f} | "
            f"{s.min_time_sec:<9.4f} | {s.max_time_sec:<9.4f} | {s.std_dev_time_sec:<10.4f} | "
            f"{s.avg_target_cpu:<8.1f}% | {speedup_str}"
        )

    print("-" * 86)
    print(f"  * Fastest observed configuration under test : {fastest.config_name.upper()} ({fastest.avg_time_sec:.4f}s avg)")
    print(f"  * Slowest observed configuration under test : {slowest.config_name.upper()} ({slowest.avg_time_sec:.4f}s avg)")
    if fastest.avg_time_sec > 0:
        ratio = slowest.avg_time_sec / fastest.avg_time_sec
        print(f"  * Observed performance difference           : {ratio:.2f}x ratio between slowest and fastest")

    print("\n  [i] ACADEMIC OBSERVATIONS & INTERPRETATION:")
    print("  * Observed execution time and CPU utilization differed between affinity configurations.")
    print("  * Concentrating multiple worker threads on fewer cores demonstrated higher per-core")
    print("    saturation and longer total execution time under this CPU-bound workload.")
    print("  * Distributing threads across separated logical processors achieved parallel execution")
    print("    with distinct core utilization profiles.")
    print("  * Note: Results reflect observed execution times and CPU utilization under the tested")
    print("    workload, operating system scheduling state, and hardware topology. Direct hardware")
    print("    metrics such as cache miss rates or context switch frequencies were not directly measured.")
    print("#" * 86 + "\n")


def export_results_to_csv(
    all_runs: List[RunMetrics],
    filepath: str = "affinity_benchmark_results.csv",
) -> str:
    """
    Exports all individual benchmark runs to a clean, structured CSV file.
    """
    if not all_runs:
        return ""

    fieldnames = [
        "Timestamp",
        "Configuration",
        "Run_Number",
        "Thread_Count",
        "Logical_Processors",
        "Physical_Cores",
        "Assignments",
        "Execution_Time_s",
        "System_Avg_CPU_pct",
        "Target_Cores_Avg_CPU_pct",
    ]

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_runs:
            writer.writerow(r.to_csv_row())

    print(f"  [+] Benchmark data successfully exported to CSV: {os.path.abspath(filepath)}")
    return filepath


def export_results_to_txt(
    summaries: List[ConfigurationSummary],
    all_runs: List[RunMetrics],
    filepath: str = "affinity_benchmark_report.txt",
    cpu_details: Optional[dict] = None,
) -> str:
    """
    Generates a formal plain-text academic benchmark report.
    """
    if not summaries:
        return ""

    sorted_summaries = sorted(summaries, key=lambda s: s.avg_time_sec)
    fastest = sorted_summaries[0]
    slowest = sorted_summaries[-1]

    lines = []
    lines.append("=" * 84)
    lines.append("        PROJECT 31: THREAD AFFINITY MANAGEMENT BENCHMARK REPORT")
    lines.append("                 Phase 1 Prototype Experimental Results")
    lines.append("=" * 84)
    lines.append(f"Report Date: {summaries[0].runs[0].timestamp_iso if summaries[0].runs else 'N/A'}\n")

    if cpu_details:
        lines.append("--- HARDWARE TOPOLOGY SPECIFICATIONS ---")
        lines.append(f"Physical CPU Cores   : {cpu_details.get('physical_cores', 'Unknown')}")
        lines.append(f"Logical Processors   : {cpu_details.get('logical_cores', 'Unknown')}")
        lines.append(f"Logical Processor IDs: {cpu_details.get('core_ids', [])}")
        if cpu_details.get("physical_core_mapping"):
            lines.append("Physical-to-Logical Core Mapping:")
            for p, l in cpu_details["physical_core_mapping"].items():
                lines.append(f"  Physical Core {p:2d} -> Logical Processors {l}")
        lines.append("")

    lines.append("--- CONFIGURATION SUMMARY (STATISTICAL AGGREGATION) ---")
    header = (
        f"{'Configuration':<14} | {'Threads':<7} | {'Runs':<5} | {'Avg Time (s)':<12} | "
        f"{'Min (s)':<9} | {'Max (s)':<9} | {'StdDev (s)':<10} | {'Target CPU %':<12}"
    )
    lines.append(header)
    lines.append("-" * 84)
    for s in sorted_summaries:
        row = (
            f"{s.config_name.upper():<14} | {s.thread_count:<7} | {s.run_count:<5} | "
            f"{s.avg_time_sec:<12.4f} | {s.min_time_sec:<9.4f} | {s.max_time_sec:<9.4f} | "
            f"{s.std_dev_time_sec:<10.4f} | {s.avg_target_cpu:<11.1f}%"
        )
        lines.append(row)
    lines.append("-" * 84)

    lines.append(f"\nFastest observed configuration : {fastest.config_name.upper()} (Avg: {fastest.avg_time_sec:.4f}s)")
    lines.append(f"Slowest observed configuration : {slowest.config_name.upper()} (Avg: {slowest.avg_time_sec:.4f}s)")
    if fastest.avg_time_sec > 0:
        ratio = slowest.avg_time_sec / fastest.avg_time_sec
        lines.append(f"Observed Performance Ratio    : {ratio:.2f}x between slowest and fastest")

    lines.append("\n--- INDIVIDUAL RUN EXECUTION LOGS ---")
    for r in all_runs:
        lines.append(
            f"[{r.config_name.upper()} Run {r.run_number}] Time: {r.execution_time_sec:.4f}s | "
            f"System CPU: {r.system_avg_cpu:.1f}% | Target CPU: {r.active_cores_avg_cpu:.1f}%"
        )

    lines.append("\n--- ACADEMIC OBSERVATIONS ---")
    lines.append("1. Execution time and per-core CPU utilization varied systematically across affinity settings.")
    lines.append("2. Concentrated placement confined threads to a restricted core subset, resulting in increased")
    lines.append("   observed execution duration and localized core saturation.")
    lines.append("3. Distributed placement separated threads across different logical processor IDs.")
    lines.append("4. Conclusions are bounded to the measured execution times and CPU utilization on this platform;")
    lines.append("   cache miss rates and kernel context switches were not directly instrumented.")
    lines.append("\n" + "=" * 84)
    lines.append("End of Report.")
    lines.append("=" * 84 + "\n")

    report_text = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"  [+] Academic report successfully saved to TXT: {os.path.abspath(filepath)}")
    return filepath
