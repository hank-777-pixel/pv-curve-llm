"""
See v_2(p_2) in the notes.
"""

import numpy as np
import matplotlib.pyplot as plt

def generate_pv_curve_two_bus(v1_ref=1.0, xL=0.5, power_factor=0.95, n_points=300):
    """
    Generates a full theoretical P-V curve for a 2-bus system.

    Parameters:
        v1_ref (float): Slack bus voltage in pu.
        xL (float): Line reactance in pu.
        power_factor (float): Load power factor (e.g., 0.95 for lagging).
        n_points (int): Number of points to compute.
    """
    phi = np.arccos(power_factor)
    tan_phi = np.tan(phi)

    P_max_estimate = v1_ref**2 / (4 * xL)
    P_vals = np.linspace(0.0, P_max_estimate * 1.5, n_points)

    V_upper = []
    V_lower = []

    for p2 in P_vals:
        a = p2 * tan_phi * xL - (v1_ref ** 2) / 2
        discriminant = a ** 2 - (xL ** 2) * (p2 ** 2) * (1 + tan_phi ** 2)

        if discriminant >= 0:
            sqrt_disc = np.sqrt(discriminant)
            v2_upper = np.sqrt(-a + sqrt_disc)
            v2_lower = np.sqrt(-a - sqrt_disc) if (-a - sqrt_disc) > 0 else np.nan

            V_upper.append(v2_upper)
            V_lower.append(v2_lower)
        else:
            V_upper.append(np.nan)
            V_lower.append(np.nan)

    V_upper = np.array(V_upper)
    V_lower = np.array(V_lower)

    # Compute dynamic axis limits (exclude NaNs)
    all_v = np.concatenate([V_upper[~np.isnan(V_upper)], V_lower[~np.isnan(V_lower)]])
    all_p = np.concatenate([P_vals[~np.isnan(V_upper)], P_vals[~np.isnan(V_lower)]])

    v_min = max(np.min(all_v) - 0.1, 0)
    v_max = np.max(all_v) + 0.1

    p_min = 0
    p_max = np.max(all_p) * 1.1

    # Find nose point
    valid_idx = ~np.isnan(V_upper)
    if np.any(valid_idx):
        nose_idx = np.where(valid_idx)[0][-1]
        nose_P = P_vals[nose_idx]
        nose_V = V_upper[nose_idx]
    else:
        nose_P, nose_V = None, None

    # Plot
    plt.figure(figsize=(8, 6))
    plt.plot(P_vals, V_upper, label="Stable branch", color="blue")
    plt.plot(P_vals, V_lower, label="Unstable branch", color="orange", linestyle="--")
    if nose_P is not None:
        plt.scatter(nose_P, nose_V, color="red", label="Nose Point")
        plt.annotate(
            f"P={nose_P:.2f} pu\nV={nose_V:.2f} pu",
            xy=(nose_P, nose_V),
            xytext=(nose_P * 0.7, nose_V + 0.1),
            arrowprops=dict(arrowstyle="->", color="black"),
            fontsize=9
        )
    plt.xlabel("Active Power P2 (pu)")
    plt.ylabel("Voltage at Bus 2 V2 (pu)")
    plt.title(f"2-Bus Theoretical P–V Curve\nv1_ref={v1_ref}, xL={xL}, PF={power_factor}")
    plt.grid(True)
    plt.legend()

    # Dynamically adjust limits
    plt.xlim(p_min, p_max)
    plt.ylim(v_min, v_max)
    plt.show()

if __name__ == "__main__":
    v1 = float(input("Enter slack bus voltage v1_ref (e.g., 1.0): ") or 1.0)
    xL = float(input("Enter line reactance xL (e.g., 0.5): ") or 0.5)
    pf = float(input("Enter power factor (e.g., 0.95): ") or 0.95)

    generate_pv_curve_two_bus(v1_ref=v1, xL=xL, power_factor=pf)
