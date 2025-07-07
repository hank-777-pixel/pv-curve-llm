from pv_curve import run_pv_curve


def main():
    """
    Locally test pv_curve.py used by the agent.
    """
    grid_choices = "ieee14/ieee24/ieee30/ieee39/ieee57/ieee118/ieee300"
    grid = input(f"Grid ({grid_choices}) [ieee39]: ").strip().lower() or "ieee39"
    bus_default = 5 if grid == "ieee39" else 10
    bus_id = int(input(f"Bus index [{bus_default}]: ") or bus_default)

    voc_stc = float(input("Voc at STC (V) [40]: ") or 40)
    isc_stc = float(input("Isc at STC (A) [9]: ") or 9)
    vmpp_stc = float(input("Vmpp at STC (V) [32]: ") or 32)
    impp_stc = float(input("Impp at STC (A) [8]: ") or 8)

    mu_voc = float(input("Voc temp-coeff per °C (-0.002): ") or -0.002)
    mu_isc = float(input("Isc temp-coeff per °C (0.0005): ") or 0.0005)
    t_cell = float(input("Cell temperature °C [25]: ") or 25)

    g_levels = [float(x) for x in (input("Irradiance list W/m² [1000]: ") or "1000").split(",")]
    n_pts = int(input("Number of IV samples [400]: ") or 400)

    result = run_pv_curve(
        grid=grid,
        bus_id=bus_id,
        voc_stc=voc_stc,
        isc_stc=isc_stc,
        vmpp_stc=vmpp_stc,
        impp_stc=impp_stc,
        mu_voc=mu_voc,
        mu_isc=mu_isc,
        t_cell=t_cell,
        g_levels=g_levels,
        n_pts=n_pts,
    )
    print(result)


if __name__ == "__main__":
    main() 