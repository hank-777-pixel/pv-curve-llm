import numpy as np
import matplotlib.pyplot as plt

def two_bus_pv_curve():
    V_s = 1.0  # Slack bus voltage (pu)
    X = 0.5    # Line reactance (pu)

    # Array of load active power P (pu), from 0 to theoretical maximum
    P_vals = np.linspace(0.0, V_s**2 / (4 * X) * 0.999, 300)
    V_upper = []
    V_lower = []

    for P in P_vals:
        discriminant = V_s**2 - 4 * P * X

        if discriminant >= 0:
            sqrt_disc = np.sqrt(discriminant)
            Vp = (V_s + sqrt_disc) / 2
            Vm = (V_s - sqrt_disc) / 2
            V_upper.append(Vp)
            V_lower.append(Vm)
        else:
            V_upper.append(np.nan)
            V_lower.append(np.nan)

    V_upper = np.array(V_upper)
    V_lower = np.array(V_lower)

    # Find nose point (last valid point before no solution)
    valid_idx = ~np.isnan(V_upper)
    nose_idx = np.where(valid_idx)[0][-1]
    nose_P = P_vals[nose_idx]
    nose_V = V_upper[nose_idx]

    # Plot
    plt.figure(figsize=(8, 6))
    plt.plot(P_vals, V_upper, label="Stable branch", color="blue")
    plt.plot(P_vals, V_lower, label="Unstable branch", color="orange", linestyle="--")
    plt.scatter(nose_P, nose_V, color="red", label="Nose Point")
    plt.annotate(
        f"P={nose_P:.2f} pu\nV={nose_V:.2f} pu",
        xy=(nose_P, nose_V),
        xytext=(nose_P * 0.7, nose_V + 0.1),
        arrowprops=dict(arrowstyle="->", color="black"),
        fontsize=9
    )
    plt.xlabel("Load Active Power P (pu)")
    plt.ylabel("Voltage Magnitude at Load Bus (pu)")
    plt.title("Full Theoretical P–V Curve for Simple 2-Bus System")
    plt.grid(True)
    plt.legend()
    plt.ylim(0, 1.2)
    plt.xlim(0, P_vals[-1])
    plt.show()

if __name__ == "__main__":
    two_bus_pv_curve()
