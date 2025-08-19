import numpy as np
import matplotlib.pyplot as plt

# 2-bus system (Example C, Part 2)
V2 = 1
PL0 = 0.5
QL0 = 0.1

x = np.array([[-0.2796, 0.906, 0]])
d = 0.3 # Tangent vector coefficient
sigma = 0.5


while x[-1, 2] >= 0:
    theta1  = x[-1, 0]
    V1      = x[-1, 1]
    p       = x[-1, 2]
    
    ## Predictor
    # Augmented Jacobian matrix

    AJ = np.array([[2*V1*V2*np.cos(theta1),     2*V2*np.sin(theta1),        1],
                   [2*V1*V2*np.sin(theta1),     4*V1-2*V2*np.cos(theta1),   0],
                   [0,                          0,                          1]])
    
    # If step size over noise point, search vertically
    if len(x[:, 0]) == 1:
        b = np.array([0, 0, d])
    elif x[-1, 2] - x[-2, 2] > 0:
        b = np.array([0, 0, d])
    else:
        b = np.array([0, 0, -d])
    
    t = np.linalg.inv(AJ) @ b
    tmax = np.max(np.abs(t))
    index = np.argmax(np.abs(t))
    t = d * t / np.max(np.abs(t))
    xp = x[-1, :] + sigma * t
    

    ## Corrector
    # Initial value
    xc = np.array([xp])
    # Obtaining variables
    theta1 = xc[-1, 0]
    V1 = xc[-1, 1]
    p = xc[-1, 2]
    
    # Function evaluation
    g = np.array([PL0 + p + 2*V1*V2*np.sin(theta1),
                  QL0 + 2*V1**2 - 2*V1*V2*np.cos(theta1)])
    # Error calculation
    error = np.max(np.abs(g))
    
    while error > 1e-4:
        AJ = np.array([[2*V1*V2*np.cos(theta1), 2*V2*np.sin(theta1), 1],
                       [2*V1*V2*np.sin(theta1), 4*V1-2*V2*np.cos(theta1), 0],
                       [0, 0, 0]])
        AJ[2, index] = 1
        delta = -np.linalg.inv(AJ) @ np.array([g[0], g[1], 0])
        xc = np.vstack([xc, xc[-1, :] + delta])
        
        theta1 = xc[-1, 0]
        V1 = xc[-1, 1]
        p = xc[-1, 2]
        
        g = np.array([PL0 + p + 2*V1*V2*np.sin(theta1),
                      QL0 + 2*V1**2 - 2*V1*V2*np.cos(theta1)])
        
        error = np.max(np.abs(g))
    
    x = np.vstack([x, xc[-1, :]])

plt.figure(1)
plt.plot(PL0 + x[:, 2], x[:, 0], 'k', linewidth=1.5)
plt.xlabel('P_L=P_{L0}+p      p.u.')
plt.ylabel('\\theta_1  rad')

plt.figure(2)
plt.plot(PL0 + x[:, 2], x[:, 1], 'k', linewidth=1.5)
plt.xlabel('P_L=P_{L0}+p      p.u.')
plt.ylabel('V_1  p.u.')

plt.show()
