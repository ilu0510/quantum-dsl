# rq5_ir_overhead_min.py
# Purpose: RQ5 (minimal) — measure overhead of IR generation only:
#   - Build IR time
#   - Canon time
#   - Peak memory
# No extraction, no compilation, no execution.

import json
import os
import time
import tracemalloc
from dataclasses import dataclass, asdict
from datetime import datetime
from statistics import mean, median

from dsl import *
from pennylane import numpy as np


def now_ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def ms(dt_seconds: float) -> float:
    return 1000.0 * dt_seconds


@dataclass
class IRMinRecord:
    benchmark: str
    repetition: int
    width: int
    n_ops: int
    n_measures: int
    t_build_ir_ms: float
    t_canon_ms: float
    peak_mem_kb: float


def count_ops(program):
    ops = program.ir.ops
    n_meas = sum(1 for x in ops if not hasattr(x, "name"))
    n_ops = len(ops) - n_meas
    return n_ops, n_meas


# ----------------------------
# One-time BLOCK registration
# ----------------------------

_BLOCKS_REGISTERED = False

def register_blocks_once():
    global _BLOCKS_REGISTERED
    if _BLOCKS_REGISTERED:
        return
    _BLOCKS_REGISTERED = True

    # Bell
    @BLOCK("bell")
    def bell():
        SUPERPOSE(0)
        ENTANGLE(0, 1)

    # Deutsch–Jozsa
    @BLOCK("oracle_x0")
    def oracle_x0(x0, x1, a):
        gate.CNOT((x0, a))

    @BLOCK("dj_2bit")
    def dj_2bit(oracle, x0, x1, a):
        gate.X(a)
        SUPERPOSE(a, x0, x1)
        USE(oracle, x0=x0, x1=x1, a=a)
        SUPERPOSE(x0, x1)
        MEASURE("probs", x0, x1)

    # Grover
    @BLOCK("oracle_grover")
    def oracle_grover():
        gate.X(0, 2)
        gate.CTRL("Z", [0, 2], 1)
        gate.X(0, 2)

    @BLOCK("diffusion")
    def diffusion():
        SUPERPOSE(0, 1, 2)
        gate.X(0, 1, 2)
        gate.CTRL("Z", [0, 1], 2)
        gate.X(0, 1, 2)
        SUPERPOSE(0, 1, 2)

    # QFT
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

    # VQE ansatz
    @BLOCK("vqe_ansatz")
    def vqe_ansatz(params):
        theta0 = params[0]
        gate.RY(theta0, 0)
        gate.CNOT((0, 1))


# ----------------------------
# Benchmarks: return (program, width)
# ----------------------------

def bench_bell():
    with PREPARE(2) as p:
        USE("bell")
        MEASURE("probs", 0, 1)
    return p, 2

def bench_dj_oracle_x0():
    with PREPARE(3) as p:
        USE("dj_2bit", oracle="oracle_x0", x0=0, x1=1, a=2)
    return p, 3

def bench_grover():
    with PREPARE(3) as p:
        SUPERPOSE(0, 1, 2)
        USE("oracle_grover")
        USE("diffusion")
        USE("oracle_grover")
        USE("diffusion")
        MEASURE("probs", 0, 1, 2)
    return p, 3

def bench_qft4():
    with PREPARE(4) as p:
        gate.X(0, 1, 2)
        USE("qft", [0, 1, 2, 3])
        MEASURE("state")
    return p, 4

def bench_vqe_expval():
    H = (obs.X(0) @ obs.X(1))
    with PREPARE(2) as p:
        USE("vqe_ansatz", [0.1])
        MEASURE("expval", hamiltonian=H)
    return p, 2


BENCHES = {
    "bell": bench_bell,
    "dj_oracle_x0": bench_dj_oracle_x0,
    "grover": bench_grover,
    "qft4": bench_qft4,
    "vqe_expval": bench_vqe_expval,
}


# ----------------------------
# Timing harness
# ----------------------------

def run_one(bench_name: str, repetition: int) -> IRMinRecord:
    register_blocks_once()

    tracemalloc.start()
    mem0 = tracemalloc.get_traced_memory()[0]

    # 1) Build IR
    t0 = time.perf_counter()
    p, width = BENCHES[bench_name]()
    t_build_ir_ms = ms(time.perf_counter() - t0)

    # 2) Canon
    t0 = time.perf_counter()
    p.ir.canon()
    t_canon_ms = ms(time.perf_counter() - t0)

    cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mem_kb = (peak - mem0) / 1024.0

    n_ops, n_meas = count_ops(p)

    return IRMinRecord(
        benchmark=bench_name,
        repetition=repetition,
        width=width,
        n_ops=n_ops,
        n_measures=n_meas,
        t_build_ir_ms=t_build_ir_ms,
        t_canon_ms=t_canon_ms,
        peak_mem_kb=peak_mem_kb,
    )


def run_suite(R: int = 20, outdir: str = "rq5_ir_min_logs"):
    ensure_dir(outdir)
    register_blocks_once()

    records = []
    for bench_name in BENCHES.keys():
        for r in range(R):
            records.append(run_one(bench_name, r))

    runs_path = os.path.join(outdir, f"rq5_ir_runs_{now_ts()}.json")
    with open(runs_path, "w", encoding="utf-8") as f:
        json.dump([asdict(x) for x in records], f, indent=2)

    summary = {}
    for bench_name in BENCHES.keys():
        subset = [x for x in records if x.benchmark == bench_name]

        def agg(field):
            vals = [getattr(x, field) for x in subset]
            return {"mean": mean(vals), "median": median(vals), "min": min(vals), "max": max(vals)}

        summary[bench_name] = {
            "width": subset[0].width,
            "n_ops": subset[0].n_ops,
            "n_measures": subset[0].n_measures,
            "t_build_ir_ms": agg("t_build_ir_ms"),
            "t_canon_ms": agg("t_canon_ms"),
            "peak_mem_kb": agg("peak_mem_kb"),
        }

    summary_path = os.path.join(outdir, f"rq5_ir_summary_{now_ts()}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[RQ5-IR] Per-run logs: {runs_path}")
    print(f"[RQ5-IR] Summary:     {summary_path}")


if __name__ == "__main__":
    run_suite(R=20)