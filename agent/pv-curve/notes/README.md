# Notes
Notes on PV Curves and their calculation.

# **Power System Modelling and Scripting** By Federico Milano
https://books.google.com/books?id=MQu7IqoLrfYC&pg=PA106#v=onepage&q&f=false

## Equations
p_2(v_2):

![Equation 1](equation1.png)

**Variables**
- **p₂**: Active power delivered to the load at bus 2 (in per-unit or MW)
- **v₂**: Voltage magnitude at bus 2 (load bus) in per-unit
- **v₂^ref**: Reference voltage magnitude at bus 2 (typically 1.0 per-unit)
- **x_L**: Line reactance between the source and load bus (in per-unit)
- **φ₂**: Power factor angle at bus 2 (phase angle between voltage and current)
- **tan φ₂**: Tangent of the power factor angle (relates to Q/P ratio)

v_2(p_2):

![Equation 2](equation2.png)

## Notes
Some relevant remarks on (5.1) are:

1. The system is characterized by a maximum value of the load power, say p₂^max, which is known as *maximum loading condition*.

2. For p₂ > p₂^max the power flow equations (5.1) have no solution. For this reason, the power flow solution for p₂ = p₂^max is known as *point of collapse*. In physical terms, this means that the system cannot supply a load whose power is p₂ > p₂^max. Thus, p₂^max is the maximum power that can be transmitted by the network and it can be considered a limit of the transmission system.

3. For p₂ < p₂^max, there are two values of v₂ that solve (5.1). However, only the solution with the higher v₂ value (*upper solution*) is physically acceptable. The other value (*lower solution*) has only a mathematical interest.

4. The shape of the PV curve is independent of the load power factor, as well as of system parameters. In other words, any network of any size and complexity shows a similar relationship between bus voltage magnitudes and load powers. PV curves are inherent the structure of classical power flow equations. As a matter of fact, as shown in (4.16) or (4.18), these have a quadratic dependence on bus voltages.
