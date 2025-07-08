import numpy as np
import matplotlib.pyplot as plt
import pandapower as pp
import pandapower.networks as pn

def generate_pv_curve_ieee39(target_bus_idx=5, step_size=0.02, max_scale=2.0, power_factor=0.95, voltage_limit=0.4):
    """
    Generate P–V curve for a selected bus in IEEE 39-bus system using numerical power flow.

    Parameters:
        target_bus_idx (int): Bus index to monitor voltage collapse.
        step_size (float): Incremental scaling factor for load increase.
        max_scale (float): Maximum scale factor to try before stopping.
        power_factor (float): Desired power factor for the added load (lagging).
        voltage_limit (float): Minimum voltage limit to stop the simulation.
    """
    # Load IEEE 39 test system
    net = pn.case39()

    # Save original load values
    net.load["p_mw_base"] = net.load["p_mw"]
    net.load["q_mvar_base"] = net.load["q_mvar"]

    results = []

    scale = 1.0
    converged = True

    while scale <= max_scale and converged:
        # Scale all loads uniformly
        for idx in net.load.index:
            net.load.at[idx, "p_mw"] = net.load.at[idx, "p_mw_base"] * scale
            net.load.at[idx, "q_mvar"] = net.load.at[idx, "p_mw"] * np.tan(np.arccos(power_factor))

        try:
            pp.runpp(net, init="results")
            v_mag = net.res_bus.at[target_bus_idx, "vm_pu"]
            total_p = net.load["p_mw"].sum()

            results.append((total_p, v_mag))

            if v_mag < voltage_limit:
                print("Voltage below limit — stopping further loading.")
                break

        except pp.LoadflowNotConverged:
            print("Power flow did not converge — collapse point reached.")
            converged = False
            break

        scale += step_size

    if not results:
        print("No valid data points found.")
        return

    P_vals, V_vals = zip(*results)

    # Find approximate "nose" point (last successful point)
    nose_P = P_vals[-1]
    nose_V = V_vals[-1]

    # Plot
    plt.figure(figsize=(8, 6))
    plt.plot(P_vals, V_vals, marker="o", linestyle="-", color="blue", label="P–V Curve")
    plt.scatter(nose_P, nose_V, color="red", label="Approx. Nose Point")
    plt.annotate(
        f"P={nose_P:.1f} MW\nV={nose_V:.3f} pu",
        xy=(nose_P, nose_V),
        xytext=(nose_P * 0.7, nose_V + 0.05),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=9
    )
    plt.xlabel("Total System Load P (MW)")
    plt.ylabel(f"Voltage at Bus {target_bus_idx} (pu)")
    plt.title(f"IEEE 39-Bus P–V Curve at Bus {target_bus_idx}")
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    target_bus = int(input("Enter target bus index (e.g., 5): ") or 5)
    generate_pv_curve_ieee39(target_bus_idx=target_bus, step_size=0.02, max_scale=2.0, power_factor=0.95)
