import numpy as np
import pandapower as pp
import pandapower.networks as pn
import matplotlib.pyplot as plt
import os


def pv_mpp_from_iv(v_points: np.ndarray, i_points: np.ndarray) -> float:
    """Return maximum power (MW) from given I–V points.

    The arrays are assumed to describe a single module/string in units of volts
    and amps. The power is converted to megawatts by dividing by 1e6.
    """
    return (v_points * i_points).max() / 1e6

# TODO: Custom networks
def integrate_pv_into_ieee39(bus_id: int = 5,
                             v_points: np.ndarray | None = None,
                             i_points: np.ndarray | None = None,
                             plot: bool = True):
    """Run a two-step simulation that couples a PV I–V curve with the IEEE-39 grid.

    1. Solve the base-case power flow for the IEEE-39 test network.
    2. Derive the PV maximum-power point (MPP) from the supplied I–V data and
       insert it as a static generator (sgen) at bus_id.
    3. Re-run the power flow with the PV injection and return the solved network
       plus the injected power.

    Parameters
    ----------
    bus_id
        Index of the bus where the PV unit is connected (0-based pandapower
        index, **not** the original IEEE numbering).
    v_points, i_points
        NumPy arrays describing the measured I–V curve.  If omitted, a simple
        synthetic curve (Isc = 8 A, Voc = 40 V, 100 points) is used.
    plot
        Whether to plot the power-voltage curve.

    Returns
    -------
    tuple[pandapowerNet, float]
        The solved pandapower network and the PV active-power injection in MW.
    """
    if v_points is None or i_points is None:
        v_points = np.linspace(0.0, 40.0, 100)
        i_points = np.linspace(8.0, 0.0, 100)

    p_pv_mw = pv_mpp_from_iv(v_points, i_points)

    if plot:
        p_curve_mw = v_points * i_points / 1e6
        fig, ax = plt.subplots()
        ax.plot(p_curve_mw, v_points)
        idx_mpp = int(np.argmax(p_curve_mw))
        p_mpp = p_curve_mw[idx_mpp]
        v_mpp = v_points[idx_mpp]
        ax.scatter(p_mpp, v_mpp, color="red", zorder=5)
        ax.annotate("MPP", (p_mpp, v_mpp), textcoords="offset points", xytext=(5, -10))
        ax.set_xlabel("Power (MW)")
        ax.set_ylabel("Voltage (V)")
        ax.set_title("PV Curve – Power vs Voltage (IEEE-39)")
        ax.grid(True)
        os.makedirs("generated", exist_ok=True)
        fig.savefig("generated/pv_curve_ieee39.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    net = pn.case39()
    pp.runpp(net)

    pp.create_sgen(net, bus=bus_id, p_mw=p_pv_mw, q_mvar=0.0, name="PV_MPP")

    pp.runpp(net)
    return net, p_pv_mw


def integrate_pv_into_ieee118(bus_id: int = 10,
                             v_points: np.ndarray | None = None,
                             i_points: np.ndarray | None = None,
                             plot: bool = True):

    if v_points is None or i_points is None:
        v_points = np.linspace(0.0, 40.0, 100)
        i_points = np.linspace(8.0, 0.0, 100)

    p_pv_mw = pv_mpp_from_iv(v_points, i_points)

    if plot:
        p_curve_mw = v_points * i_points / 1e6
        fig, ax = plt.subplots()
        ax.plot(p_curve_mw, v_points)
        idx_mpp = int(np.argmax(p_curve_mw))
        p_mpp = p_curve_mw[idx_mpp]
        v_mpp = v_points[idx_mpp]
        ax.scatter(p_mpp, v_mpp, color="red", zorder=5)
        ax.annotate("MPP", (p_mpp, v_mpp), textcoords="offset points", xytext=(5, -10))
        ax.set_xlabel("Power (MW)")
        ax.set_ylabel("Voltage (V)")
        ax.set_title("PV Curve – Power vs Voltage (IEEE-118)")
        ax.grid(True)
        os.makedirs("generated", exist_ok=True)
        fig.savefig("generated/pv_curve_ieee118.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    net = pn.case118()
    pp.runpp(net)

    pp.create_sgen(net, bus=bus_id, p_mw=p_pv_mw, q_mvar=0.0, name="PV_MPP")

    pp.runpp(net)
    return net, p_pv_mw


if __name__ == "__main__":
    choice = input("Choose grid (ieee39/ieee118) [ieee39]: ").strip().lower() or "ieee39"
    if choice == "ieee118":
        _net, _p_pv = integrate_pv_into_ieee118()
    else:
        _net, _p_pv = integrate_pv_into_ieee39()

    print("PV injected power (MW):", _p_pv)
    print(_net.res_bus.head()) 