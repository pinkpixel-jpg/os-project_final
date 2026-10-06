# 🧵 Project 31 – Thread Affinity Management: Coding Task List

> **Phase 1 – What we actually need to build**
> Share this with the team. Only code implementation tasks are listed here.

---

## Module 1 — CPU Core Detection
- [ ] Detect the number of logical CPU cores available on the machine
- [ ] Store the list of available core IDs (e.g., `[0, 1, 2, 3]`)
- [ ] Print/display the detected core count at program start

---

## Module 2 — Worker Thread Creation
- [ ] Accept a configurable number of worker threads (e.g., via CLI arg or constant)
- [ ] Create `N` worker threads using the threading library
- [ ] Ensure threads are created cleanly and can be joined after completion

---

## Module 3 — Workload Engine
- [ ] Implement a **repeatable, CPU-intensive workload** to run on each thread
  - Suggested: prime number calculation, matrix multiply, or busy loop with fixed iterations
- [ ] Workload must be deterministic (same input → same compute time across runs)
- [ ] Keep the workload function separate so it can be reused in all configurations

---

## Module 4 — Thread Affinity Management
Implement **4 affinity configurations** (this is the core of the project):

- [ ] **Config 1 – Baseline:** Create and run threads with **no explicit affinity** set (OS decides scheduling)
- [ ] **Config 2 – Fixed (1:1 pinning):** Pin each thread to a **dedicated core** (Thread 0 → Core 0, Thread 1 → Core 1, …)
- [ ] **Config 3 – Distributed:** Spread threads across **all available cores** in a round-robin or even spread
- [ ] **Config 4 – Concentrated:** Force **all threads onto 1 or 2 cores** only

> **OS API to use:**
> - **Windows:** `SetThreadAffinityMask()` via `ctypes` / `pywin32`
> - **Linux:** `os.sched_setaffinity()` (Python 3.3+) or `pthread_setaffinity_np` via ctypes
> - **Cross-platform option:** `psutil.Process().cpu_affinity([...])` 

- [ ] Write a reusable `set_affinity(thread, core_list)` function used by all 4 configs
- [ ] Verify affinity is actually applied (read back the CPU affinity mask after setting)

---

## Module 5 — Performance Measurement
Collect the following for each configuration run:

- [ ] **Execution time** — wall-clock time from thread start to all threads joined (`time.perf_counter()`)
- [ ] **Thread count** — log how many threads were used
- [ ] **Core count** — log how many cores were available
- [ ] **Thread-to-core assignment** — log which core(s) each thread was assigned to
- [ ] *(Optional but good)* **CPU utilization per core** — sample `psutil.cpu_percent(percpu=True)` during workload execution

---

## Module 6 — Results Display / Output
- [ ] Print a clear results table per run showing: config name, thread count, core assignment, execution time
- [ ] After all 4 configs run, print a **comparison summary** (which was fastest/slowest)
- [ ] *(Optional)* Save results to a `.csv` or `.txt` file for submission

---

## Main Program Loop (`main.py`)
- [ ] On start: detect cores → print them
- [ ] Accept number of threads (hardcode or CLI input)
- [ ] Loop through all 4 affinity configurations sequentially
- [ ] For each config: apply affinity → run workload → measure → display results
- [ ] Final comparison output at the end

---

## Suggested File Structure

```
project/
├── main.py               # Entry point, runs all 4 configs
├── cpu_detection.py      # Module 1
├── workload.py           # Module 3 – the CPU-intensive task
├── affinity_manager.py   # Module 4 – all affinity logic
├── metrics.py            # Module 5 – timing and CPU measurement
└── display.py            # Module 6 – printing and saving results
```

---

## ✅ Done Criteria (before submission)
- [ ] Program runs without errors on the demo machine
- [ ] All 4 affinity configurations execute and produce output
- [ ] Results clearly differ between configurations
- [ ] No placeholder/fake affinity functions — real OS API must be used
- [ ] Code has comments on the affinity and measurement sections
