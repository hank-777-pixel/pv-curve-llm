"""
Real PV modules do not have a linear I-V characteristic—they follow an exponential (single-diode) shape—so in practice 
V_MPP is usually around 70–80 % of V_oc.
If you replace the linear current definition with a more realistic one, the MPP in the plot will shift accordingly.
"""

import numpy as np
import pandapower as pp
import pandapower.networks as pn
import matplotlib.pyplot as plt
import os

def pv_mpp_from_iv(v_points: np.ndarray, i_points: np.ndarray) -> float:
    return (v_points * i_points).max() / 1e6


def integrate_pv(grid: str,
                bus_id: int,
                v_points: np.ndarray,
                i_points: np.ndarray,
                plot: bool = True):

    p_pv_mw = pv_mpp_from_iv(v_points, i_points)

    if plot:
        p_curve_mw = v_points * i_points / 1e6
        fig, ax = plt.subplots()
        ax.plot(p_curve_mw, v_points)
        idx_mpp = int(np.argmax(p_curve_mw))
        ax.scatter(p_curve_mw[idx_mpp], v_points[idx_mpp], color="red", zorder=5)
        ax.annotate("MPP", (p_curve_mw[idx_mpp], v_points[idx_mpp]), textcoords="offset points", xytext=(5, -10))
        ax.set_xlabel("Power (MW)")
        ax.set_ylabel("Voltage (V)")
        ax.set_title(f"PV Curve – Power vs Voltage ({grid.upper()})")
        ax.grid(True)
        os.makedirs("generated", exist_ok=True)
        fig.savefig(f"generated/pv_curve_{grid}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    net = {"ieee39": pn.case39, "ieee118": pn.case118}[grid]()
    pp.runpp(net)

    pp.create_sgen(net, bus=bus_id, p_mw=p_pv_mw, q_mvar=0.0, name="PV_MPP")

    pp.runpp(net)
    return net, p_pv_mw


if __name__ == "__main__":
    grid = input("Grid (ieee39/ieee118) [ieee39]: ").strip().lower() or "ieee39"
    default_bus = 5 if grid == "ieee39" else 10
    try:
        bus_id = int(input(f"Bus index [{default_bus}]: ") or default_bus)
    except ValueError:
        bus_id = default_bus

    try:
        voc = float(input("Open-circuit voltage Voc (V) [40]: ") or 40)
        isc = float(input("Short-circuit current Isc (A) [8]: ") or 8)
    except ValueError:
        voc, isc = 40.0, 8.0

    try:
        n_pts = int(input("Number of I-V samples (step size) [100]: ") or 100)
    except ValueError:
        n_pts = 100

    v_arr = np.linspace(0.0, voc, n_pts)
    i_arr = np.linspace(isc, 0.0, n_pts)

    _net, _p_pv = integrate_pv(grid, bus_id, v_arr, i_arr)

    print("PV injected power (MW):", _p_pv)
    print(_net.res_bus.head()) 