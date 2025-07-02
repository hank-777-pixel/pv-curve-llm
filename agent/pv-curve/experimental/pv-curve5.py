import numpy as np
import pandapower as pp
import pandapower.networks as pn
import matplotlib.pyplot as plt
import os


def iv_curve_exponential(voc: float, isc: float, n_pts: int, alpha: float = 5.0):
    """Generate non-linear I-V points using a simple exponential model.

    I(V) = Isc * (1 – exp((V – Voc) / (Voc / alpha)))

    • V = 0  ⇒ I ≈ Isc (short-circuit)
    • V = Voc ⇒ I = 0  (open-circuit)

    The shape parameter alpha controls curvature; 5–10 yields
    V_MPP ≈ 0.7 × Voc for typical silicon PV modules.
    """
    v = np.linspace(0.0, voc, n_pts)
    delta = voc / alpha
    i = isc * (1.0 - np.exp((v - voc) / delta))
    return v, i


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
        fig.savefig(f"generated/pv_curve_{grid}_exp.png", dpi=300, bbox_inches="tight")
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
        n_pts = int(input("Number of I-V samples (step size) [200]: ") or 200)
    except ValueError:
        n_pts = 200

    try:
        alpha = float(input("Curvature parameter alpha (5–10 typical) [5]: ") or 5)
    except ValueError:
        alpha = 5.0

    v_arr, i_arr = iv_curve_exponential(voc, isc, n_pts, alpha)

    _net, _p_pv = integrate_pv(grid, bus_id, v_arr, i_arr)

    print("PV injected power (MW):", _p_pv)
    print(_net.res_bus.head())
