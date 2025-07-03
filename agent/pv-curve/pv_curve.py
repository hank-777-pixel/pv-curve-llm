import numpy as np
import pandapower as pp
import pandapower.networks as pn
import matplotlib.pyplot as plt
import os
from typing import List, Tuple


def compute_alpha(voc: float, isc: float, vmpp: float, impp: float) -> float:
    """Return positive curvature parameter derived from STC points.

    Variables
    - voc: open-circuit voltage (V)
    - isc: short-circuit current (A)
    - vmpp: voltage at maximum-power-point (V)
    - impp: current at maximum-power-point (A)

    The exponential IV model uses:

        I(V) = Isc * (1 - exp((V - Voc) / δ))

    where δ (delta) is obtained from datasheet MPP coordinates. Solving
    Impp = Isc * (1 - exp((Vmpp - Voc) / δ)) gives:

        δ = (Vmpp - Voc) / ln(1 - Impp / Isc)
    """
    frac = 1.0 - impp / isc
    if frac <= 0:
        raise ValueError("Impp must be smaller than Isc for a valid PV curve")
    return voc * np.log(frac) / (vmpp - voc)


def iv_curve(voc: float, isc: float, alpha: float, n_pts: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate exponential I-V arrays for given parameters.

    Variables
    - voc: open-circuit voltage (V)
    - isc: short-circuit current (A)
    - alpha: curvature constant (dimensionless)
    - n_pts: number of sample points
    """
    v = np.linspace(0.0, voc, n_pts)
    delta = voc / alpha
    i = isc * (1.0 - np.exp((v - voc) / delta))
    return v, i


def adjust_stc(
    voc_stc: float,
    isc_stc: float,
    mu_voc: float,
    mu_isc: float,
    gc: float,
    t_cell: float,
) -> Tuple[float, float]:
    """Scale Voc and Isc from STC to specified irradiance and temperature.

    Variables
    - voc_stc / isc_stc: STC open-circuit volts / short-circuit amps
    - mu_voc / mu_isc: temperature coefficients per °C
    - gc: irradiance (W m⁻²)
    - t_cell: cell temperature (°C)
    """
    voc = voc_stc * (1.0 + mu_voc * (t_cell - 25.0))
    isc = isc_stc * (1.0 + mu_isc * (t_cell - 25.0)) * (gc / 1000.0)
    return voc, isc


def pv_mpp(v: np.ndarray, i: np.ndarray) -> Tuple[float, float]:
    """Return power in MW and voltage at maximum-power-point.

    Variables
    - v: voltage array (V)
    - i: current array (A)
    Returns
    - p_mw: max power (MW)
    - v_mpp: voltage at MPP (V)
    """
    p = v * i
    idx = int(np.argmax(p))
    return p[idx] / 1e6, v[idx]


def integrate_pv(grid: str, bus_id: int, p_mw: float):
    """Run power flow with PV injection on a selected IEEE test network.

    Supported grids (pandapower.networks):
    - ieee14, ieee24, ieee30, ieee39, ieee57, ieee118, ieee300

    Variables
    - grid: selected grid name
    - bus_id: bus index where PV is connected
    - p_mw: injected active power (MW)
    """
    net_map = {
        "ieee14": pn.case14,
        "ieee24": pn.case24_ieee_rts,
        "ieee30": pn.case30,
        "ieee39": pn.case39,
        "ieee57": pn.case57,
        "ieee118": pn.case118,
        "ieee300": pn.case300,
    }

    if grid not in net_map:
        raise ValueError(f"Unsupported grid '{grid}'. Choose from {list(net_map)}")

    net = net_map[grid]()
    pp.runpp(net)
    pp.create_sgen(net, bus=bus_id, p_mw=p_mw, q_mvar=0.0, name="PV_MPP")
    pp.runpp(net)
    return net


def run_pv_curve(
    grid: str = "ieee39",
    bus_id: int = 5,
    voc_stc: float = 41.0,
    isc_stc: float = 8.9,
    vmpp_stc: float = 34.0,
    impp_stc: float = 8.2,
    mu_voc: float = -0.0023,
    mu_isc: float = 0.0005,
    t_cell: float = 25.0,
    g_levels: List[float] | None = None,
    n_pts: int = 400,
) -> str:
    """Compute PV curves, inject power into the grid, return summary string.

    Key Inputs
    - grid: network case ("ieee39" / "ieee118")
    - bus_id: bus index for PV plant
    - voc_stc, isc_stc, vmpp_stc, impp_stc: STC electrical points
    - mu_voc, mu_isc: temperature-coefficients
    - t_cell: cell temperature (°C)
    - g_levels: list of irradiances (W m⁻²)
    - n_pts: samples per curve
    Returns a printable summary string.
    """
    g_levels = g_levels or [1000.0]

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
        ax.annotate(f"{p_mw:.3f} MW", (p_mw, v_mpp), textcoords="offset points", xytext=(5, -10))
    ax.set_xlabel("Power (MW)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title(f"PV Curves – {grid.upper()} (T={t_cell}°C)")
    ax.grid(True)
    ax.legend()
    fig_path = f"generated/pv_curves_{grid}_multi.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    net = integrate_pv(grid, bus_id, curves[0][3])

    summary = (
        f"PV curves saved to {fig_path}\n"
        f"PV injected power (MW): {curves[0][3]:.4f}\n"
        f"{net.res_bus.head().to_string()}"
    )
    return summary
