import numpy as np
import matplotlib.pyplot as plt

# --------------- Parameters -----------------
codes = ["bit-flip", "phase-flip", "depolarizing"]
n_qubits = 1048576
p_vals = np.linspace(0, 1, 41)
threshold_QEC = {"bit-flip": 0.5, "phase-flip": 0.5, "depolarizing": 0.5}
# AUIL "universal" threshold is always p=1/n_qubits for this toy model
threshold_AUIL = {c: 1.0 / n_qubits for c in codes}
n_runs = 500000  # for statistics in "live" traces

# --------------- QEC Logical Survival Functions -------------
def logical_survival(code, p):
    if code in ["bit-flip", "phase-flip"]:
        return (1 - p) ** n_qubits + n_qubits * p * (1 - p) ** (n_qubits - 1)
    elif code == "depolarizing":
        # For simple depolarizing channel (bit/phase flips both possible)
        return (1 - p) ** n_qubits
    else:
        raise ValueError("Unknown code")

def AUIL_signal(code, p):
    # Universal: signal = max(0, 1 - n_qubits*p)
    # (Only a *single* signal survives unless p < 1/n_qubits)
    return np.maximum(0, 1 - n_qubits * p)

# --------- Data Aggregation ----------
QEC_curves = {}
AUIL_curves = {}
for code in codes:
    QEC_curves[code] = np.array([logical_survival(code, p) for p in p_vals])
    AUIL_curves[code] = np.array([AUIL_signal(code, p) for p in p_vals])

# --------- Multi-panel Plotting -------------
fig, axes = plt.subplots(3, 2, figsize=(16, 14))
fig.suptitle("Quantum Noise Filtering: AUIL as Universal Noise Threshold Detector", fontsize=18, fontweight="bold")

# ---- 1. Logical Info Survived vs Noise p (per code, both QEC & AUIL) ----
for idx, code in enumerate(codes):
    ax = axes[0, 0]
    ax.plot(p_vals, QEC_curves[code], label=f"{code.title()} QEC", lw=2)
    ax.plot(p_vals, AUIL_curves[code], "--", label=f"{code.title()} AUIL", lw=2)
    # Vertical threshold lines
    ax.axvline(threshold_QEC[code], color="gray", ls=":", lw=1)
    ax.axvline(threshold_AUIL[code], color="brown", ls="--", lw=1)
ax.set_ylabel("Fraction of logical info survived")
ax.set_xlabel("Noise probability $p$")
ax.set_title("Logical Info Survived (All Codes/Models)")
ax.legend()
ax.grid(True, alpha=0.3)

# ---- 2. Heatmap: Survival Fraction (QEC & AUIL) ----
heatmap_data = []
for code in codes:
    heatmap_data.append(QEC_curves[code])
im = axes[0, 1].imshow(np.array(heatmap_data), aspect="auto", extent=[0, 1, 0, len(codes)],
                       origin="lower", cmap="viridis")
axes[0, 1].set_yticks(np.arange(len(codes))+0.5)
axes[0, 1].set_yticklabels([c.title() for c in codes])
axes[0, 1].set_xlabel("Noise probability $p$")
axes[0, 1].set_title("QEC Logical Survival Heatmap")
plt.colorbar(im, ax=axes[0, 1], orientation='vertical', shrink=0.75, pad=0.02, label="Fraction Survived")

# ---- 3. Threshold Comparison Bar Chart ----
width = 0.35
x = np.arange(len(codes))
axes[1, 0].bar(x-width/2, [threshold_QEC[c] for c in codes], width, label="QEC Threshold")
axes[1, 0].bar(x+width/2, [threshold_AUIL[c] for c in codes], width, label="AUIL Threshold")
axes[1, 0].set_xticks(x)
axes[1, 0].set_xticklabels([c.title() for c in codes])
axes[1, 0].set_ylabel("Threshold $p$")
axes[1, 0].set_ylim(0, 1)
axes[1, 0].set_title("Noise Thresholds: QEC vs AUIL")
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.2)

# ---- 4. Residual/Error Plot (QEC - AUIL per code) ----
for code in codes:
    diff = QEC_curves[code] - AUIL_curves[code]
    axes[1, 1].plot(p_vals, diff, label=f"{code.title()}", lw=2)
axes[1, 1].axhline(0, color='k', ls=':', alpha=0.5)
axes[1, 1].set_xlabel("Noise probability $p$")
axes[1, 1].set_ylabel("QEC - AUIL")
axes[1, 1].set_title("Residual (QEC - AUIL Signal)")
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.2)

# ---- 5. Single Run Trace (simulated) ----
np.random.seed(42)
single_run_p = np.linspace(0, 1, 50)
single_code = "bit-flip"
logical_bits = np.ones(len(single_run_p))
# Simulate logical survival: at each p, logical survives with prob given by QEC_curve
for i, p in enumerate(single_run_p):
    survive = np.random.rand() < logical_survival(single_code, p)
    logical_bits[i] = survive
AUIL_bits = (AUIL_signal(single_code, single_run_p) > 0).astype(float)
axes[2, 0].plot(single_run_p, logical_bits, 'o-', label="Logical Survival (QEC)", alpha=0.7)
axes[2, 0].plot(single_run_p, AUIL_bits, 'x--', label="AUIL Signal", alpha=0.7)
axes[2, 0].axvline(threshold_QEC[single_code], color="gray", ls=":", lw=1)
axes[2, 0].axvline(threshold_AUIL[single_code], color="brown", ls="--", lw=1)
axes[2, 0].set_title(f"Single Run: Logical & AUIL (Code: {single_code})")
axes[2, 0].set_xlabel("Noise probability $p$")
axes[2, 0].set_ylabel("Signal Detected")
axes[2, 0].legend()
axes[2, 0].grid(True, alpha=0.2)

# ---- 6. (Optional) ROC-style plot: True/False Positive rates ----
# Here we can fake a "classifier": QEC = ground truth, AUIL = prediction
# (for demo: for each p, treat QEC > 0.5 as "signal", AUIL > 0.5 as detected)
true_pos, false_pos = [], []
for code in codes:
    truth = (QEC_curves[code] > 0.5).astype(int)
    pred = (AUIL_curves[code] > 0.5).astype(int)
    tp = np.mean((truth == 1) & (pred == 1))
    fp = np.mean((truth == 0) & (pred == 1))
    true_pos.append(tp)
    false_pos.append(fp)
axes[2, 1].plot(false_pos, true_pos, 'o-', label="AUIL (vs QEC truth)")
axes[2, 1].plot([0,1], [0,1], "k--", alpha=0.5)
axes[2, 1].set_xlabel("False Positive Rate")
axes[2, 1].set_ylabel("True Positive Rate")
axes[2, 1].set_title("AUIL as Universal Signal Detector (ROC Curve)")
axes[2, 1].legend()
axes[2, 1].grid(True, alpha=0.2)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()
