from pv_curve import generate_pv_curve


def main():
    """
    Locally test pv_curve.py used by the agent.
    """
    grid_choices = "ieee14/ieee24/ieee30/ieee39/ieee57/ieee118/ieee300"
    grid_key = input(f"Grid ({grid_choices}) [ieee39]: ").strip().lower() or "ieee39"

    bus_default = 5 if grid_key == "ieee39" else 10
    bus_id = int(input(f"Bus index [{bus_default}]: ") or bus_default)

    step_size = float(input("Load step size [0.01]: ") or 0.01)
    max_scale = float(input("Max load scale [3.0]: ") or 3.0)
    power_factor = float(input("Power factor [0.95]: ") or 0.95)
    voltage_limit = float(input("Voltage limit pu [0.4]: ") or 0.4)
    save_path = input("Save path [generated/pv_curve_voltage_stability.png]: ").strip() or "generated/pv_curve_voltage_stability.png"

    generate_pv_curve(
        grid=grid_key,
        target_bus_idx=bus_id,
        step_size=step_size,
        max_scale=max_scale,
        power_factor=power_factor,
        voltage_limit=voltage_limit,
        save_path=save_path,
    )


if __name__ == "__main__":
    main() 