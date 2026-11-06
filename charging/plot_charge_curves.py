"""Plot both measured charge curves of the Magicshine EVO 1700 UT from charge-curves.csv (SVG + PNG).

Usage: python3 plot_charge_curves.py   (requires matplotlib; run inside the charging/ folder)
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

runs = {}
for r in csv.DictReader(open("charge-curves.csv", encoding="utf-8")):
    d = runs.setdefault(r["run"], {"t": [], "p": [], "e": []})
    d["t"].append(float(r["time_min"]))
    d["p"].append(float(r["power_w_corrected"]))
    d["e"].append(float(r["energy_wh_corrected"]))

STYLE = {"1": ("#2a78d6", "Run 1 · 2026-11-02 · from empty · 3:08 h · 19.54 Wh"),
         "2": ("#eb6834", "Run 2 · 2026-11-04 · from <10 % · 3:09 h · 19.10 Wh*")}
INK, SUB, GRID = "#0b0b0b", "#52514e", "#e1e0d9"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#c3c2b7",
                     "axes.labelcolor": SUB, "xtick.color": SUB, "ytick.color": SUB, "svg.fonttype": "none"})

fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True, gridspec_kw={"hspace": 0.22})
fig.text(0.08, 0.965, "Magicshine EVO 1700 UT – measured charge curves", fontsize=14, fontweight="bold", color=INK)
fig.text(0.08, 0.935, "USB input side, 5 V · Anker Nano II 45 W charger · YOJOCK USB power meter", fontsize=9, color=SUB)

for ax, key, label, ymax, step in [(a1, "p", "Input power (W)", 11.5, 2), (a2, "e", "Energy charged (Wh)", 21, 5)]:
    for n, d in runs.items():
        c, lab = STYLE[n]
        ax.plot(d["t"], d[key], color=c, lw=1.8, label=lab, solid_joinstyle="round", solid_capstyle="round")
    ax.set_ylabel(label)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_locator(MultipleLocator(step))
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)

a1.legend(loc="upper center", bbox_to_anchor=(0.5, 1.27), ncol=1, frameon=False, fontsize=9, handlelength=1.6)
a1.text(38, 10.85, "constant current (CC)", ha="center", fontsize=9, color=SUB)
a1.text(140, 10.85, "constant voltage (CV)", ha="center", fontsize=9, color=SUB)
a2.annotate("End: 19.54 / 19.10 Wh (USB side)", xy=(189, 19.3), xytext=(150, 11.5), fontsize=9, color=INK,
            ha="center", arrowprops=dict(arrowstyle="-", color="#898781", lw=0.8))
a2.set_xlim(0, 195)
a2.xaxis.set_major_locator(MultipleLocator(30))
a2.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v // 60)}:{int(v % 60):02d}"))
a2.set_xlabel("Charging time (h:mm)")
fig.text(0.08, 0.012,
         "Estimated cell capacity (run 1): 19.54 Wh × ~0.88 charger efficiency ÷ ~4.0 V ≈ 4.3 Ah (≈ 15.5 Wh at 3.6 V)\n"
         "Rated: 5200 mAh / 18.7 Wh (3.6 V)\n"
         "*Run 2 started with a small remaining charge; 4 min of light use during charging removed (−0.38 Wh)",
         fontsize=8.5, color=SUB)
fig.subplots_adjust(left=0.08, right=0.975, top=0.81, bottom=0.135)
fig.savefig("charge-curves.svg", facecolor="white")
fig.savefig("charge-curves.png", dpi=200, facecolor="white")
