"""
See v_2(p_2) in the notes.
Same as pv-curve11.py, but with comments. Only supporst 2-bus system.
"""

import numpy as np
import matplotlib.pyplot as plt

def generate_pv_curve_two_bus(v1_ref=1.0, xL=0.5, power_factor=0.95, n_points=300):
    """
    Generates a theoretical P–V curve for a simple 2-bus system.

    Parameters:
        v1_ref (float): Voltage at the first bus (slack bus), usually 1.0 per unit (pu).
        xL (float): Reactance (impedance) of the transmission line between bus 1 and bus 2 (in pu).
        power_factor (float): Power factor of the load at bus 2 (e.g., 0.95 means slightly inductive).
        n_points (int): Number of points to sample for the curve.
    """
    # Compute the angle of the load power factor (phi)
    # phi = arccos(power factor), describes how much current lags voltage
    phi = np.arccos(power_factor)
    tan_phi = np.tan(phi)

    # Estimate a rough maximum power at which voltage might collapse
    # This is a theoretical guess to help choose a range for P
    P_max_estimate = v1_ref**2 / (4 * xL)

    # Create an array of possible load power values (P2) from 0 to about 1.5 times P_max_estimate
    P_vals = np.linspace(0.0, P_max_estimate * 1.5, n_points)

    # Store calculated voltages for stable and unstable solutions
    V_upper = []
    V_lower = []

    for p2 in P_vals:
        # Intermediate variable 'a' derived from voltage equation (theoretical expression)
        a = p2 * tan_phi * xL - (v1_ref ** 2) / 2

        # Discriminant inside the square root (must be non-negative for real solutions)
        discriminant = a ** 2 - (xL ** 2) * (p2 ** 2) * (1 + tan_phi ** 2)

        if discriminant >= 0:
            sqrt_disc = np.sqrt(discriminant)

            # First possible voltage solution (higher voltage, usually stable)
            v2_upper = np.sqrt(-a + sqrt_disc)

            # Second possible voltage solution (lower voltage, usually unstable)
            v2_lower = np.sqrt(-a - sqrt_disc) if (-a - sqrt_disc) > 0 else np.nan

            V_upper.append(v2_upper)
            V_lower.append(v2_lower)
        else:
            # No real voltage solution possible (after collapse), mark as NaN
            V_upper.append(np.nan)
            V_lower.append(np.nan)

    # Convert to numpy arrays for easier handling
    V_upper = np.array(V_upper)
    V_lower = np.array(V_lower)

    # Combine all valid voltages and powers to find plot limits
    all_v = np.concatenate([V_upper[~np.isnan(V_upper)], V_lower[~np.isnan(V_lower)]])
    all_p = np.concatenate([P_vals[~np.isnan(V_upper)], P_vals[~np.isnan(V_lower)]])

    # Set voltage axis limits (dynamic), add margin
    v_min = max(np.min(all_v) - 0.1, 0)
    v_max = np.max(all_v) + 0.1

    # Set power axis limits (dynamic), add margin
    p_min = 0
    p_max = np.max(all_p) * 1.1

    # Find "nose point" — the highest loading point before voltage collapse
    valid_idx = ~np.isnan(V_upper)
    if np.any(valid_idx):
        nose_idx = np.where(valid_idx)[0][-1]
        nose_P = P_vals[nose_idx]
        nose_V = V_upper[nose_idx]
    else:
        nose_P, nose_V = None, None

    # Plotting
    plt.figure(figsize=(8, 6))
    plt.plot(P_vals, V_upper, label="Stable branch", color="blue")
    plt.plot(P_vals, V_lower, label="Unstable branch", color="orange", linestyle="--")

    # Mark the nose point
    if nose_P is not None:
        plt.scatter(nose_P, nose_V, color="red", label="Nose Point (Collapse)")
        plt.annotate(
            f"P={nose_P:.2f} pu\nV={nose_V:.2f} pu",
            xy=(nose_P, nose_V),
            xytext=(nose_P * 0.7, nose_V + 0.1),
            arrowprops=dict(arrowstyle="->", color="black"),
            fontsize=9
        )

    plt.xlabel("Active Power at Bus 2, P2 (pu)")
    plt.ylabel("Voltage at Bus 2, V2 (pu)")
    plt.title(f"2-Bus Theoretical P–V Curve\nv1_ref={v1_ref}, xL={xL}, PF={power_factor}")
    plt.grid(True)
    plt.legend()

    plt.xlim(p_min, p_max)
    plt.ylim(v_min, v_max)
    plt.show()

if __name__ == "__main__":
    # Prompt user for inputs
    v1 = float(input("Enter slack bus voltage v1_ref (e.g., 1.0): ") or 1.0)
    xL = float(input("Enter line reactance xL (e.g., 0.5): ") or 0.5)
    pf = float(input("Enter power factor (e.g., 0.95): ") or 0.95)

    generate_pv_curve_two_bus(v1_ref=v1, xL=xL, power_factor=pf)
