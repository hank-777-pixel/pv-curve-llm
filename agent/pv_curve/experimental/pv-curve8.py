import numpy as np
import matplotlib.pyplot as plt
import pandapower as pp
import pandapower.networks as pn


def generate_pv_curve(
    network_loader=pn.case39,
    target_bus_idx=5,
    step_size=0.02,
    max_scale=2.0,
    power_factor=0.95,
    voltage_limit=0.6,
    save_path="pv_curve_voltage_stability.png"
):
    """
    Generates a classic system-level P–V (power-voltage) curve for voltage stability analysis.

    Parameters:
        network_loader: Function that returns a pandapower network (e.g., pn.case39)
        target_bus_idx: Bus index to monitor for voltage collapse
        step_size: Load increase step (e.g., 0.02 for 2% increments)
        max_scale: Maximum load multiplier (e.g., 2.0 for 200%)
        power_factor: Constant power factor for scaling loads
        voltage_limit: Voltage threshold (pu) to stop iteration
        save_path: Path to save the final PV curve plot
    """
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

            print(f"Scale: {scale:.2f}  Total P: {total_p:.2f} MW  Voltage at bus {target_bus_idx}: {v_mag:.4f} pu")
            results.append((total_p, v_mag))

            if v_mag < voltage_limit:
                print("Voltage below threshold. Likely near collapse point.")
                break

        except pp.LoadflowNotConverged:
            print("Power flow did not converge. Collapse point reached.")
            converged = False
            break

        scale += step_size

    P_vals, V_vals = zip(*results)

    plt.figure(figsize=(8, 6))
    plt.plot(P_vals, V_vals, marker="o", linestyle="-", color="blue")
    plt.xlabel("Total Active Load P (MW)")
    plt.ylabel(f"Voltage at Bus {target_bus_idx} (pu)")
    plt.title("System P–V Curve (Voltage Stability)")
    plt.grid(True)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"\nP–V curve saved to {save_path}")


if __name__ == "__main__":      
    generate_pv_curve(
        network_loader=pn.case39,
        target_bus_idx=5,
        step_size=0.02,
        max_scale=2.0,
        power_factor=0.95
    )
