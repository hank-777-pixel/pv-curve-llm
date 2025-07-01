import numpy as np
import matplotlib.pyplot as plt
import os

def pv_curve(x_l=0.3, phi_deg=0.0, v1_ref=1.0, v2_min=0.5, v2_max=1.3, n=200):
    """Generate and plot a PV (P–V) curve for a simple radial 2-bus system.

    Args:
        x_l (float): Line reactance between the source and load bus (p.u.).
        phi_deg (float): Load power-factor angle φ₂ in degrees (lagging +).
        v1_ref (float): Sending-end (source) voltage magnitude v₁ʳᵉᶠ (p.u.).
        v2_min (float): Minimum load-bus voltage to evaluate (p.u.).
        v2_max (float): Maximum load-bus voltage to evaluate (p.u.).
        n (int): Number of evaluation points.
        show (bool): If true, display the curve using matplotlib.

    Returns:
        tuple[np.ndarray, np.ndarray]: Arrays of v₂ and p₂ values.
    """
    phi = np.radians(phi_deg)
    t = np.tan(phi)
    a = t ** 2

    v2 = np.linspace(v2_min, v2_max, n)
    rad = a - (1 - (v1_ref**2) / (v2**2))
    rad[rad < 0] = np.nan
    root = np.sqrt(rad)

    p2 = (v2**2 / x_l) * ((-t + root) / (1 + a))

    # Plot
    fig, ax = plt.subplots()
    ax.plot(p2, v2)
    ax.set_xlabel('P₂ (p.u.)')
    ax.set_ylabel('V₂ (p.u.)')
    ax.set_title('PV Curve')
    ax.grid(True)

    os.makedirs("generated", exist_ok=True)
    fig.savefig("generated/pv_curve.png", dpi=300, bbox_inches="tight")

    return v2, p2


if __name__ == "__main__":
    try:
        x_l = float(input("Line reactance x_L (default 0.3): ") or 0.3)
        phi_deg = float(input("Load power-factor angle φ₂ in degrees (default 0): ") or 0.0)
    except ValueError:
        print("Invalid input, using defaults.")
        x_l, phi_deg = 0.3, 0.0

    pv_curve(x_l=x_l, phi_deg=phi_deg)