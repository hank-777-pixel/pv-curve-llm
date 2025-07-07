import numpy as np
import matplotlib.pyplot as plt
import pandapower as pp
import pandapower.networks as pn
import os

# TODO: This is a work in progress with many issues currently.
def pv_curve_pp(
    grid: str = "ieee39",
    bus_id: int | None = None,
    step_mw: float = 10.0,
    n_steps: int = 40,
    base_p: float | None = None,
    pf_deg: float = 0.0,
    v_stop: float = 0.5,
):
    """Generate and save a PV curve using pandapower.

    Args:
        grid:  "ieee39" or "ieee118" (currently supported IEEE test cases).
        bus_id: Bus index to be stressed; defaults to the first load bus.
        step_mw: Active-power increment (ΔP) per iteration (MW).
        n_steps: Maximum number of increments.
        base_p: Base-case active power at *bus_id* (MW) **if the bus has no load**.
        pf_deg: Power-factor angle φ (deg, lagging +) for the new load.
        v_stop: Stop simulation when V at *bus_id* falls below this p.u. value.

    Returns:
        Tuple of NumPy arrays ``(p_array, v_array)``.
    """
    net = {
        "ieee39": pn.case39,
        "ieee118": pn.case118,
    }[grid]()

    if bus_id is None:
        bus_id = int(net.load.bus.iloc[0])

    # Ensure there is a load at the selected bus
    if net.load[net.load.bus == bus_id].empty:
        if base_p is None:
            raise ValueError("Selected bus has no load – provide base_p.")
        phi = np.radians(pf_deg)
        q_new = base_p * np.tan(phi)
        net.make_load(bus_id, p_mw=base_p, q_mvar=q_new, name="pv_base")

    load_idx = net.load[net.load.bus == bus_id].index[0]
    base_p_existing = float(net.load.at[load_idx, "p_mw"])
    base_q_existing = float(net.load.at[load_idx, "q_mvar"])

    if base_p_existing == 0:
        tan_phi = np.tan(np.radians(pf_deg))
    else:
        tan_phi = base_q_existing / base_p_existing

    # Handle generators at the stressed bus:
    # If the bus hosts a generator (PV bus), unlimited reactive support
    # keeps the voltage high.  Set realistic Q-limits so it will switch
    # to PQ when limits are hit, letting the classic nose shape appear.
    gens_at_bus = net.gen[net.gen.bus == bus_id].index.tolist()
    for g in gens_at_bus:
        net.gen.at[g, "max_q_mvar"] = 200.0  # arbitrary ± 200 MVar
        net.gen.at[g, "min_q_mvar"] = -200.0

    # Also enforce reactive limits globally
    runpp_kwargs = dict(max_iteration=50, tolerance_mva=1e-3, init="results", enforce_q_lims=True)

    p_vals, v_vals = [], []
    for k in range(n_steps):
        p = base_p_existing + step_mw * k
        q = p * tan_phi
        net.load.at[load_idx, "p_mw"] = p
        net.load.at[load_idx, "q_mvar"] = q
        try:
            pp.runpp(net, **runpp_kwargs)
        except pp.LoadflowNotConverged:
            break
        v = net.res_bus.vm_pu.at[bus_id]
        p_vals.append(p)
        v_vals.append(v)
        if v < v_stop:
            break

    p_arr, v_arr = np.array(p_vals), np.array(v_vals)

    fig, ax = plt.subplots()
    ax.plot(p_arr, v_arr)
    ax.set_xlabel("P (MW)")
    ax.set_ylabel("V (p.u.)")
    ax.set_title(f"PV Curve – {grid.upper()} Bus {bus_id}")
    ax.grid(True)
    os.makedirs("generated", exist_ok=True)
    fig.savefig(f"generated/pv_curve_{grid}_bus{bus_id}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    return p_arr, v_arr


if __name__ == "__main__":
    grid = input("Grid size (ieee39 / ieee118) [ieee39]: ").strip() or "ieee39"

    temp_net = {"ieee39": pn.case39, "ieee118": pn.case118}[grid]()
    load_buses = sorted(set(temp_net.load.bus.tolist()))
    print("Existing load buses:", ", ".join(map(str, load_buses)))

    bus_raw = input("Bus index to stress [enter for first load bus]: ").strip()
    bus_id = int(bus_raw) if bus_raw else None

    base_p = None
    pf_deg = 0.0
    if bus_id is not None and bus_id not in load_buses:
        try:
            base_p = float(input("Selected bus has no load. Enter base active power P0 [MW]: ") or 10.0)
        except ValueError:
            base_p = 10.0
        try:
            pf_deg = float(input("Power-factor angle φ (deg, lag +) [0]: ") or 0.0)
        except ValueError:
            pf_deg = 0.0

    step = float(input("Step size ΔP MW [10]: ") or 10.0)
    steps = int(input("Number of steps [40]: ") or 40)
    v_stop = float(input("Stop when V drops below [0.5 p.u.]: ") or 0.5)

    p, v = pv_curve_pp(
        grid=grid,
        bus_id=bus_id,
        step_mw=step,
        n_steps=steps,
        base_p=base_p,
        pf_deg=pf_deg,
        v_stop=v_stop,
    )

    if len(p) and v[-1] < v_stop + 0.05:
        print("Voltage collapse approaching – curve nose reached.") 