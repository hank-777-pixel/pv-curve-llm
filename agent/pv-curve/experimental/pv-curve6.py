"""
Work in progress.
"""

import numpy as np
import pandapower as pp
import pandapower.networks as pn
import matplotlib.pyplot as plt
import os
from typing import List, Tuple


def compute_alpha(voc: float, isc: float, vmpp: float, impp: float) -> float:
    """Return curvature parameter derived from datasheet STC points."""
    return (voc - vmpp) / (voc * np.log(1.0 - impp / isc))


def iv_curve(voc: float, isc: float, alpha: float, n_pts: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate exponential I-V arrays for given parameters."""
    v = np.linspace(0.0, voc, n_pts)
    delta = voc / alpha
    i = isc * (1.0 - np.exp((v - voc) / delta))
    return v, i


def adjust_stc(voc_stc: float, isc_stc: float, mu_voc: float, mu_isc: float, gc: float, t_cell: float) -> Tuple[float, float]:
    """Scale Voc and Isc from STC to given irradiance and temperature."""
    voc = voc_stc * (1.0 + mu_voc * (t_cell - 25.0))
    isc = isc_stc * (1.0 + mu_isc * (t_cell - 25.0)) * (gc / 1000.0)
    return voc, isc


def pv_mpp(v: np.ndarray, i: np.ndarray) -> Tuple[float, float]:
    """Return power in MW and voltage at maximum power point."""
    p = v * i
    idx = int(np.argmax(p))
    return p[idx] / 1e6, v[idx]


def integrate_pv(grid: str, bus_id: int, p_mw: float):
    """Run power flow with PV static generator injection."""
    net = {"ieee39": pn.case39, "ieee118": pn.case118}[grid]()
    pp.runpp(net)
    pp.create_sgen(net, bus=bus_id, p_mw=p_mw, q_mvar=0.0, name="PV_MPP")
    pp.runpp(net)
    return net


if __name__ == "__main__":
    grid = input("Grid (ieee39/ieee118) [ieee39]: ").strip().lower() or "ieee39"
    default_bus = 5 if grid == "ieee39" else 10
    try:
        bus_id = int(input(f"Bus index [{default_bus}]: ") or default_bus)
    except ValueError:
        bus_id = default_bus

    try:
        voc_stc = float(input("Voc at STC (V) [40]: ") or 40)
        isc_stc = float(input("Isc at STC (A) [8]: ") or 8)
        vmpp_stc = float(input("Vmpp at STC (V) [32]: ") or 32)
        impp_stc = float(input("Impp at STC (A) [7]: ") or 7)
    except ValueError:
        voc_stc, isc_stc, vmpp_stc, impp_stc = 40.0, 8.0, 32.0, 7.0

    try:
        mu_voc = float(input("Voc temp coeff frac per °C (-0.0023): ") or -0.0023)
        mu_isc = float(input("Isc temp coeff frac per °C (0.0005): ") or 0.0005)
    except ValueError:
        mu_voc, mu_isc = -0.0023, 0.0005

    try:
        t_cell = float(input("Cell temperature °C [25]: ") or 25)
    except ValueError:
        t_cell = 25.0

    g_list_raw = input("Irradiance list W/m^2, comma separated [1000]: ").strip() or "1000"
    try:
        g_levels: List[float] = [float(x) for x in g_list_raw.split(",")]
    except ValueError:
        g_levels = [1000.0]

    try:
        n_pts = int(input("Number of I-V samples [300]: ") or 300)
    except ValueError:
        n_pts = 300

    alpha = compute_alpha(voc_stc, isc_stc, vmpp_stc, impp_stc)

    curves = []
    for g in g_levels:
        voc, isc = adjust_stc(voc_stc, isc_stc, mu_voc, mu_isc, g, t_cell)
        v, i = iv_curve(voc, isc, alpha, n_pts)
        p_mw, v_mpp = pv_mpp(v, i)
        curves.append((g, v, i, p_mw, v_mpp))

    os.makedirs("generated", exist_ok=True)
    fig, ax = plt.subplots()
    for g, v, i, p_mw, v_mpp in curves:
        p_curve_mw = v * i / 1e6
        ax.plot(p_curve_mw, v, label=f"G={g} W/m²")
        ax.scatter(p_mw, v_mpp, s=20)
    ax.set_xlabel("Power (MW)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title(f"PV Curves – {grid.upper()} (T={t_cell}°C)")
    ax.grid(True)
    ax.legend()
    fig.savefig(f"generated/pv_curves_{grid}_multi.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    net = integrate_pv(grid, bus_id, curves[0][3])
    print("PV injected power (MW):", curves[0][3])
    print(net.res_bus.head()) 