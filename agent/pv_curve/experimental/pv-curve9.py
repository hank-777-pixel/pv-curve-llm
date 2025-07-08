import numpy as np
import matplotlib.pyplot as plt
import pandapower as pp
import pandapower.networks as pn

def generate_pv_curve(
    network_loader=pn.case39,
    target_bus_idx=5,
    step_size=0.01,
    max_scale=3.0,
    power_factor=0.95,
    voltage_limit=0.4,
    save_path="generated/pv_curve_voltage_stability.png"
):
    net = network_loader()

    net.load["p_mw_base"] = net.load["p_mw"]
    net.load["q_mvar_base"] = net.load["q_mvar"]

    scale_buses = list(net.load["bus"].values)
    results = []

    scale = 1.0
    converged = True

    while scale <= max_scale and converged:
        for idx in net.load.index:
            if net.load.at[idx, "bus"] in scale_buses:
                base_p = net.load.at[idx, "p_mw_base"]
                net.load.at[idx, "p_mw"] = base_p * scale
                net.load.at[idx, "q_mvar"] = net.load.at[idx, "p_mw"] * np.tan(np.arccos(power_factor))

        try:
            pp.runpp(net, init="results")
            v_mag = net.res_bus.at[target_bus_idx, "vm_pu"]
            total_p = net.load["p_mw"].sum()

            results.append((total_p, v_mag))

            if v_mag < voltage_limit:
                print("Voltage below limit, stopping.")
                break

        except pp.LoadflowNotConverged:
            print("Power flow did not converge — collapse point reached.")
            converged = False
            break

        scale += step_size

    # Extract data
    P_vals, V_vals = zip(*results)

    # Find approximate "nose" point (maximum load)
    max_p_idx = np.argmax(P_vals)
    nose_p = P_vals[max_p_idx]
    nose_v = V_vals[max_p_idx]

    # Plot
    plt.figure(figsize=(8, 6))
    plt.plot(P_vals, V_vals, marker="o", linestyle="-", color="blue", label="P-V Curve")
    plt.scatter(nose_p, nose_v, color="red", zorder=5, label="Approx. Nose Point")
    plt.annotate(
        f"P={nose_p:.1f} MW\nV={nose_v:.3f} pu",
        xy=(nose_p, nose_v),
        xytext=(nose_p * 0.9, nose_v + 0.05),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=9
    )
    plt.xlabel("Total Active Load P (MW)")
    plt.ylabel(f"Voltage at Bus {target_bus_idx} (pu)")
    plt.title("System P–V Curve (Voltage Stability Analysis)")
    plt.grid(True)
    plt.legend()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"\nP–V curve saved to {save_path}")

if __name__ == "__main__":
    generate_pv_curve(
        network_loader=pn.case39,
        target_bus_idx=5,
        step_size=0.01,
        max_scale=3.0,
        power_factor=0.95
    )
