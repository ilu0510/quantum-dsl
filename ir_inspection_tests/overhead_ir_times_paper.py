import matplotlib.pyplot as plt

# 1. THE DATASET
data = {
    "2": {"t_build_ir_ms": {"mean": 0.04204, "min": 0.03630, "max": 0.08560}, "t_canon_ms": {"mean": 0.00592, "min": 0.00490, "max": 0.01620}, "peak_mem_kb": {"mean": 2.30560, "min": 1.93945, "max": 3.54883}},
    "3": {"t_build_ir_ms": {"mean": 0.05212, "min": 0.05060, "max": 0.05700}, "t_canon_ms": {"mean": 0.00858, "min": 0.00800, "max": 0.01110}, "peak_mem_kb": {"mean": 3.02402, "min": 3.02246, "max": 3.06934}},
    "4": {"t_build_ir_ms": {"mean": 0.07309, "min": 0.06880, "max": 0.11160}, "t_canon_ms": {"mean": 0.01342, "min": 0.01200, "max": 0.01410}, "peak_mem_kb": {"mean": 4.51406, "min": 4.51172, "max": 4.58203}},
    "5": {"t_build_ir_ms": {"mean": 0.08954, "min": 0.08700, "max": 0.09950}, "t_canon_ms": {"mean": 0.01818, "min": 0.01660, "max": 0.01900}, "peak_mem_kb": {"mean": 6.08223, "min": 6.07910, "max": 6.17285}},
    "6": {"t_build_ir_ms": {"mean": 0.11591, "min": 0.11090, "max": 0.14540}, "t_canon_ms": {"mean": 0.02473, "min": 0.02330, "max": 0.02770}, "peak_mem_kb": {"mean": 8.32227, "min": 8.31836, "max": 8.43555}},
    "8": {"t_build_ir_ms": {"mean": 0.17160, "min": 0.16690, "max": 0.18920}, "t_canon_ms": {"mean": 0.03902, "min": 0.03620, "max": 0.04230}, "peak_mem_kb": {"mean": 12.93203, "min": 12.92188, "max": 13.22656}},
    "10": {"t_build_ir_ms": {"mean": 0.23714, "min": 0.23060, "max": 0.26400}, "t_canon_ms": {"mean": 0.05696, "min": 0.05390, "max": 0.06500}, "peak_mem_kb": {"mean": 18.53867, "min": 18.52539, "max": 18.92383}},
    "12": {"t_build_ir_ms": {"mean": 0.32082, "min": 0.31470, "max": 0.36390}, "t_canon_ms": {"mean": 0.07739, "min": 0.07450, "max": 0.08050}, "peak_mem_kb": {"mean": 25.37070, "min": 25.34961, "max": 25.98242}},
    "14": {"t_build_ir_ms": {"mean": 0.41938, "min": 0.40870, "max": 0.45820}, "t_canon_ms": {"mean": 0.10365, "min": 0.09640, "max": 0.14030}, "peak_mem_kb": {"mean": 32.91992, "min": 32.86133, "max": 34.61914}},
    "16": {"t_build_ir_ms": {"mean": 0.54113, "min": 0.53500, "max": 0.58050}, "t_canon_ms": {"mean": 0.12975, "min": 0.12420, "max": 0.13720}, "peak_mem_kb": {"mean": 42.07305, "min": 42.02148, "max": 43.56836}}
}

# 2. DATA PROCESSING
qubits = sorted([int(k) for k in data.keys()])

# Time Metrics
t_build_mean = [data[str(q)]["t_build_ir_ms"]["mean"] for q in qubits]
t_build_min = [data[str(q)]["t_build_ir_ms"]["min"] for q in qubits]
t_build_max = [data[str(q)]["t_build_ir_ms"]["max"] for q in qubits]

t_canon_mean = [data[str(q)]["t_canon_ms"]["mean"] for q in qubits]
t_canon_min = [data[str(q)]["t_canon_ms"]["min"] for q in qubits]
t_canon_max = [data[str(q)]["t_canon_ms"]["max"] for q in qubits]

t_ir_mean = [b + c for b, c in zip(t_build_mean, t_canon_mean)]
t_ir_min = [b + c for b, c in zip(t_build_min, t_canon_min)]
t_ir_max = [b + c for b, c in zip(t_build_max, t_canon_max)]

# Memory Metrics
mem_mean = [data[str(q)]["peak_mem_kb"]["mean"] for q in qubits]
mem_min = [data[str(q)]["peak_mem_kb"]["min"] for q in qubits]
mem_max = [data[str(q)]["peak_mem_kb"]["max"] for q in qubits]

# 3. PLOTTING
# Create figure with 2 subplots vertically joined (hspace=0)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 7), sharex=True, gridspec_kw={'hspace': 0})

# --- TOP PLOT: Execution Time ---
ax1.plot(qubits, t_build_mean, label='Mean IR Build Time', color='#1f77b4', marker='o', linestyle='--')
ax1.fill_between(qubits, t_build_min, t_build_max, color='#1f77b4', alpha=0.10)

ax1.plot(qubits, t_canon_mean, label='Mean IR Canonicalisation Time', color='#2ca02c', marker='s', linestyle='--')
ax1.fill_between(qubits, t_canon_min, t_canon_max, color='#2ca02c', alpha=0.10)

ax1.plot(qubits, t_ir_mean, label='Mean Total IR Generation Time', color='#d62728', marker='^')
ax1.fill_between(qubits, t_ir_min, t_ir_max, color='#d62728', alpha=0.10)

ax1.set_ylabel('Time (ms)', fontsize=13)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='upper left', fontsize=10, frameon=True)

# --- BOTTOM PLOT: Peak Memory ---
ax2.plot(qubits, mem_mean, label='Mean Peak Memory', color='#9467bd', marker='d')
ax2.fill_between(qubits, mem_min, mem_max, color='#9467bd', alpha=0.2)

ax2.set_xlabel('Number of Qubits', fontsize=13)
ax2.set_ylabel('Memory (KB)', fontsize=13)
ax2.set_xticks(qubits)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(loc='upper left', fontsize=10, frameon=True)

# Final cleanup
plt.tight_layout()
fig.subplots_adjust(hspace=0) # Ensures plots touch exactly
plt.show()