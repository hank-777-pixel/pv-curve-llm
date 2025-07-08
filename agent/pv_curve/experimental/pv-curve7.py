import pandapower as pp
import pandapower.networks as pn
import numpy as np

net = pn.case39()

target_bus_idx = 5
scale_buses = list(net.load["bus"].values)  

net.load["p_mw_base"] = net.load["p_mw"]
net.load["q_mvar_base"] = net.load["q_mvar"]

step_size = 0.02
max_scale = 2.0
pf = 0.95

results = []

scale_factor = 1.0
converged = True

while scale_factor <= max_scale and converged:  
    for idx in net.load.index:
        if net.load.at[idx, "bus"] in scale_buses:
            p_base = net.load.at[idx, "p_mw_base"]
            net.load.at[idx, "p_mw"] = p_base * scale_factor
            net.load.at[idx, "q_mvar"] = net.load.at[idx, "p_mw"] * (np.tan(np.arccos(pf)))

    try:
        pp.runpp(net, init="results")
        
        v_mag = net.res_bus.at[target_bus_idx, "vm_pu"]
        
        total_P = net.load["p_mw"].sum()
        
        results.append((total_P, v_mag))

        if v_mag < 0.6:
            print("Voltage dangerously low: likely collapse region reached.")
            break

    except pp.LoadflowNotConverged:
        print("Power flow did not converge: system has reached voltage collapse point.")
        converged = False

    scale_factor += step_size

import matplotlib.pyplot as plt

P_vals, V_vals = zip(*results)

plt.figure(figsize=(8, 6))
plt.plot(P_vals, V_vals, marker="o", linestyle="-")
plt.xlabel("Total active load P (MW)")
plt.ylabel(f"Voltage at bus {target_bus_idx} (pu)")
plt.title("System P-V Curve (Voltage Stability Analysis)")
plt.grid(True)
plt.savefig("pv_curve_voltage_stability.png", dpi=300)
plt.close()
