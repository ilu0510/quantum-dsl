# rq5_qft_scaling.py
# Measures IR build/canon/memory for QFT as a function of qubit count.
# No compile, no execution.

import json, os, time, tracemalloc
from dataclasses import dataclass, asdict
from datetime import datetime
from statistics import mean, median
import matplotlib.pyplot as plt

from dsl import *
from pennylane import numpy as np

def now_ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

def ms(s): return 1000.0 * s

def count_ops(program):
    ops = program.ir.ops
    n_meas = sum(1 for x in ops if not hasattr(x, "name"))
    n_ops = len(ops) - n_meas
    return n_ops, n_meas

# Register once
_BLOCKS_REGISTERED = False
def register_blocks_once():
    global _BLOCKS_REGISTERED
    if _BLOCKS_REGISTERED:
        return
    _BLOCKS_REGISTERED = True

    @BLOCK("qft")
    def qft(wires):
        n = len(wires)
        for i in range(n):
            SUPERPOSE(wires[i])
            for j in range(i + 1, n):
                angle = np.pi / (2 ** (j - i))
                gate.CRZ(angle, wires[j], wires[i])
        for i in range(n // 2):
            gate.SWAP((wires[i], wires[n - 1 - i]))

@dataclass
class QFTScalingRec:
    n_qubits: int
    repetition: int
    n_ops: int
    n_measures: int
    t_build_ir_ms: float
    t_canon_ms: float
    peak_mem_kb: float

def build_qft_program(n: int):
    wires = list(range(n))
    with PREPARE(n) as p:
        # Optional: put the input in a non-trivial state.
        # Keep it cheap + deterministic:
        for w in wires[:-1]:   # mimic your "X(0,1,2)" pattern
            gate.X(w)
        USE("qft", wires)
        MEASURE("state")
    return p

def run_one(n: int, rep: int) -> QFTScalingRec:
    register_blocks_once()

    tracemalloc.start()
    mem0 = tracemalloc.get_traced_memory()[0]

    t0 = time.perf_counter()
    p = build_qft_program(n)
    t_build = ms(time.perf_counter() - t0)

    t0 = time.perf_counter()
    p.ir.canon()
    t_canon = ms(time.perf_counter() - t0)

    cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    n_ops, n_meas = count_ops(p)

    return QFTScalingRec(
        n_qubits=n,
        repetition=rep,
        n_ops=n_ops,
        n_measures=n_meas,
        t_build_ir_ms=t_build,
        t_canon_ms=t_canon,
        peak_mem_kb=(peak - mem0) / 1024.0,
    )

def summarize(recs):
    # group by n_qubits
    out = {}
    for n in sorted({r.n_qubits for r in recs}):
        subset = [r for r in recs if r.n_qubits == n]
        def agg(field):
            vals = [getattr(r, field) for r in subset]
            return {"mean": mean(vals), "median": median(vals), "min": min(vals), "max": max(vals)}
        out[n] = {
            "n_ops": subset[0].n_ops,
            "t_build_ir_ms": agg("t_build_ir_ms"),
            "t_canon_ms": agg("t_canon_ms"),
            "peak_mem_kb": agg("peak_mem_kb"),
        }
    return out

def plot_with_band(x, mean_vals, min_vals, max_vals, xlabel, ylabel, title, outpath):
    plt.figure()
    plt.plot(x, mean_vals, marker="o")
    plt.fill_between(x, min_vals, max_vals, alpha=0.15)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()


def generate_plots(summary: dict, outdir: str):
    qubits = sorted(summary.keys())

    build_mean = []
    build_min = []
    build_max = []

    canon_mean = []
    canon_min = []
    canon_max = []

    mem_mean = []
    mem_min = []
    mem_max = []

    ops = []

    for q in qubits:
        ops.append(summary[q]["n_ops"])

        b = summary[q]["t_build_ir_ms"]
        build_mean.append(b["mean"])
        build_min.append(b["min"])
        build_max.append(b["max"])

        c = summary[q]["t_canon_ms"]
        canon_mean.append(c["mean"])
        canon_min.append(c["min"])
        canon_max.append(c["max"])

        m = summary[q]["peak_mem_kb"]
        mem_mean.append(m["mean"])
        mem_min.append(m["min"])
        mem_max.append(m["max"])

    # 1) Build time vs qubits
    plot_with_band(
        qubits, build_mean, build_min, build_max,
        xlabel="Qubits (n)",
        ylabel="Build IR time (ms)",
        title="QFT IR Build Time vs Qubits",
        outpath=os.path.join(outdir, "qft_build_time_vs_qubits.png"),
    )

    # 2) Canon time vs qubits
    plot_with_band(
        qubits, canon_mean, canon_min, canon_max,
        xlabel="Qubits (n)",
        ylabel="Canon time (ms)",
        title="QFT Canon Time vs Qubits",
        outpath=os.path.join(outdir, "qft_canon_time_vs_qubits.png"),
    )

    # 3) Peak memory vs qubits
    plot_with_band(
        qubits, mem_mean, mem_min, mem_max,
        xlabel="Qubits (n)",
        ylabel="Peak memory (KB)",
        title="QFT Peak Memory vs Qubits",
        outpath=os.path.join(outdir, "qft_peak_memory_vs_qubits.png"),
    )

    # 4) Build time vs number of ops
    plot_with_band(
        ops, build_mean, build_min, build_max,
        xlabel="Number of IR operations",
        ylabel="Build IR time (ms)",
        title="QFT IR Build Time vs IR Operation Count",
        outpath=os.path.join(outdir, "qft_build_time_vs_ops.png"),
    )


if __name__ == "__main__":
    Ns = [2, 3, 4, 5, 6, 8, 10, 12, 14, 16]
    R = 30

    recs = []
    for n in Ns:
        for rep in range(R):
            recs.append(run_one(n, rep))

    outdir = "rq5_qft_scaling_logs"
    os.makedirs(outdir, exist_ok=True)

    runs_path = os.path.join(outdir, f"rq5_qft_scaling_runs_{now_ts()}.json")
    with open(runs_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in recs], f, indent=2)

    summary = summarize(recs)

    summary_path = os.path.join(outdir, f"rq5_qft_scaling_summary_{now_ts()}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Generate plots
    generate_plots(summary, outdir)

    print("[RQ5-QFT] Runs:", runs_path)
    print("[RQ5-QFT] Summary:", summary_path)
    print("[RQ5-QFT] Plots saved in:", outdir)