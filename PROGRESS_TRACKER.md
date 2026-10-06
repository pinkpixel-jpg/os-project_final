# 📋 Project 31: Thread Affinity Management — Progress & Work Tracker

This document tracks implementation progress across all 6 project modules and 3 team members, detailing what is completed, when it was completed, and verification results.

---

## 👥 Team Breakdown & Module Allocation

| Teammate | Assigned Modules | Focus Area | Status |
|---|---|---|---|
| **Teammate 1** | **Module 1 & Module 2** | CPU Core Detection & Worker Thread Creation | ✅ Completed & Verified |
| **Teammate 2** | **Module 3 & Module 4** | Workload Engine & Thread Affinity Management (OS API) | ✅ Completed & Verified |
| **Teammate 3 (You)** | **Module 5 & Module 6** | Performance Measurement, Output Reporting & End-to-End Integration | ✅ Completed & Verified |

---

## 🗂️ Complete File Structure

```text
OS_FINAL_PROJECT/
├── cpu_detection.py               # [Module 1 - Teammate 1] CPU topology & physical-to-logical discovery
├── thread_manager.py             # [Module 2 - Teammate 1] Thread creation, Native OS TID tracking, join
├── workload.py                   # [Module 3 - Teammate 2] Deterministic compute engine (GIL-releasing C hashing)
├── affinity_manager.py           # [Module 4 - Teammate 2] Windows SetThreadAffinityMask & 4 distinct policies
├── metrics.py                    # [Module 5 - Teammate 3 (You)] High-res timer, CPU sampler & multi-run stats
├── display.py                    # [Module 6 - Teammate 3 (You)] ASCII load bars, multi-run comparison & exports
├── main.py                       # [Integration] Automated repeated benchmark pipeline runner
├── test_affinity_manager.py      # Unit tests for Module 4 policy layer (25 tests passing)
├── test_modules_5_and_6.py       # Unit tests for Modules 3, 5, 6 (11 tests passing)
├── affinity_benchmark_results.csv# Exported CSV recording every individual run
├── affinity_benchmark_report.txt # Formally generated academic plain-text report
├── PROJECT_EXPLANATION_GUIDE.md  # Complete viva prep, algorithms, flowchart & architecture
├── coding_task_list.md           # Original task specification
└── PROGRESS_TRACKER.md           # This live tracking document
```

---

## ✅ Detailed Progress Checklist

### 🔹 Teammate 1: Modules 1 & 2
- [x] **M1.1: Core Count Detection** — Detect physical cores and logical processors (`os.cpu_count()`, `psutil`)  
  *Status:* `[Completed]` | *Verified:* `8 Physical Cores, 12 Logical Processors detected`  
- [x] **M1.2: Core IDs List** — Generate and store list of logical processor IDs (`[0, 1, ..., 11]`)  
  *Status:* `[Completed]` | *Verified:* `0-indexed list for Windows affinity masks`  
- [x] **M1.3: Start Display** — Display detected topology, distinguishing physical vs logical cores  
  *Status:* `[Completed]` | *Verified:* `Formatted hardware banner in console`  
- [x] **M2.1: Configurable Thread Count** — Allow setting worker thread count (CLI argument or parameter)  
  *Status:* `[Completed]` | *Verified:* `Supports arbitrary N threads`  
- [x] **M2.2: Thread Instantiation** — Cleanly create worker threads with proper targeting and arguments  
  *Status:* `[Completed]` | *Verified:* `threading.Thread wrapper`  
- [x] **M2.3: Thread Lifecycle Management** — Start and cleanly join all threads with synchronization  
  *Status:* `[Completed]` | *Verified:* `ThreadManager lifecycle with native OS TID extraction`  

---

### 🔹 Teammate 2: Modules 3 & 4
- [x] **M3.1: Deterministic Workload** — Implement a CPU-bound compute workload (SHA-256 block hashing)  
  *Status:* `[Completed]` | *Verified:* `Implemented in workload.py with GIL-releasing C hashing`  
- [x] **M3.2: Repeatability** — Ensure uniform compute duration across runs given identical inputs  
  *Status:* `[Completed]` | *Verified:* `Identical byte buffers and deterministic loops`  
- [x] **M3.3: Decoupled Design** — Package workload as a standalone reusable function  
  *Status:* `[Completed]` | *Verified:* `get_workload_function() factory`  
- [x] **M4.1: OS Affinity API (Windows)** — Implement `SetThreadAffinityMask` using `ctypes` (`kernel32`)  
  *Status:* `[Completed]` | *Verified:* `Native Win32 kernel calls via WinDLL('kernel32')`  
- [x] **M4.2: Config 1 (Baseline)** — Execute threads without explicit affinity (standard OS scheduling)  
  *Status:* `[Completed]` | *Verified:* `Empty core mask; OS scheduler freedom`  
- [x] **M4.3: Config 2 (Fixed 1:1)** — Pin each worker thread to consecutive logical processors (Thread $i \to$ Logical Core $i$)  
  *Status:* `[Completed]` | *Verified:* `Cores [0, 1, 2, 3]`  
- [x] **M4.4: Config 3 (Distributed)** — Distribute threads across separated logical processors (`[0, 3, 6, 9]`)  
  *Status:* `[Completed]` | *Verified:* `FIXED != DISTRIBUTED; threads dispersed across separate physical cores`  
- [x] **M4.5: Config 4 (Concentrated)** — Confine all threads to 1 or 2 specific cores (`[0, 1]`)  
  *Status:* `[Completed]` | *Verified:* `All threads mapped to cores [0, 1]`  
- [x] **M4.6: Affinity Verification** — Verify mask application using readback / OS query  
  *Status:* `[Completed]` | *Verified:* `verify_thread_affinity() checking return code & mask`  

---

### 🔹 Teammate 3 (You): Modules 5 & 6
- [x] **M5.1: High-Precision Wall-Clock Timing** — Measure execution time per config using `time.perf_counter()`  
  *Status:* `[Completed]` | *Verified:* `Sub-millisecond resolution timing across repeated runs`  
- [x] **M5.2: Metadata Logging** — Record active thread count, total cores, and thread-to-core mapping  
  *Status:* `[Completed]` | *Verified:* `Structured in RunMetrics dataclass`  
- [x] **M5.3: Per-Core CPU Utilization** — Asynchronously sample core utilization during workload (`psutil.cpu_percent(percpu=True)`)  
  *Status:* `[Completed]` | *Verified:* `CpuUtilizationSampler background daemon thread`  
- [x] **M5.4: Repeated Benchmarking Statistics** — Calculate mean, min, max, std dev across $K$ runs  
  *Status:* `[Completed]` | *Verified:* `aggregate_runs() computing standard deviation and averages`  
- [x] **M6.1: Run Results Table** — Render clean, formatted console table with per-core ASCII load bars  
  *Status:* `[Completed]` | *Verified:* `ASCII load bars compatible with Windows CMD/PowerShell`  
- [x] **M6.2: Comparative Summary** — Print comparative statistical table with scientifically neutral analysis  
  *Status:* `[Completed]` | *Verified:* `Ranking, speedup vs baseline, and neutral observation notes`  
- [x] **M6.3: Results Export** — Automatically persist all individual runs to `.csv` and formal `.txt` report  
  *Status:* `[Completed]` | *Verified:* `Every run recorded in affinity_benchmark_results.csv & report.txt`  
- [x] **M6.4: End-to-End Orchestration** — Integrate all 6 modules in `main.py` with `--runs N` support  
  *Status:* `[Completed]` | *Verified:* `python main.py 4 --runs 3 executes cleanly`  

---

## 📊 Live Benchmark Summary (3 Repetitions on 12-Core System)

| Configuration | Threads | Runs | Avg Time (s) | Min Time (s) | Max Time (s) | StdDev (s) | Target CPU % | Speedup vs Base |
|---|---|---|---|---|---|---|---|---|
| **BASELINE** | 4 | 3 | **0.7355 s** | 0.7283 s | 0.7444 s | 0.0082 s | 38.5% | **1.00x (Baseline)** |
| **DISTRIBUTED** | 4 | 3 | **0.7546 s** | 0.7362 s | 0.7742 s | 0.0190 s | 97.2% | **0.97x (Equal)** |
| **FIXED** | 4 | 3 | **1.0691 s** | 1.0635 s | 1.0763 s | 0.0066 s | 98.4% | **0.69x (Slower)** |
| **CONCENTRATED** | 4 | 3 | **2.1534 s** | 2.1355 s | 2.1643 s | 0.0157 s | 98.2% | **0.34x (Slower)** |

> **Key Academic Observation:**  
> - **FIXED vs DISTRIBUTED Difference:** In FIXED mode (`[0, 1, 2, 3]`), threads 0 & 1 share Physical Core 0, and threads 2 & 3 share Physical Core 1 via hyperthreading, taking **1.07s**. In DISTRIBUTED mode (`[0, 3, 6, 9]`), threads are spread across separate physical cores, completing in **0.75s**!
> - **CONCENTRATED Bottleneck:** Packing all 4 threads onto Cores 0 & 1 increased average execution time to **2.15s** (a **2.93x difference** compared to Baseline).
