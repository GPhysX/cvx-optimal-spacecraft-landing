import cvxpy as cp
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

def optimize_trajectory(K=35):
    # Parameters
    h = 1.
    g = 0.1
    m = 10.
    Fmax = 10.
    p0 = np.array([50,50,100])
    v0 = np.array([-10,0,-10])
    alpha = 0.5
    gamma = 1.
    e3 = np.array([0,0,1])

    # CVXPY problem setup
    p = cp.Variable((3,K)) # position vectors
    v = cp.Variable((3,K)) # velocity vectors
    f = cp.Variable((3,K)) # thrust vectors

    fuel = 0
    for k in range(K):
        fuel = fuel + gamma * h * cp.norm(f[:,k], 2)

    objective = cp.Minimize(fuel)
    # Initial state
    c_init = [
        p[:,0] == p0,
        v[:,0] == v0,
    ]
    # Target
    c_end = [
        p[:,-1] == 0,
        v[:,-1] == 0,
    ]
    # Maximal thrust
    c_fmax = [cp.norm(f[:,k], 2) <= Fmax  for k in range(K)]
    # Glide cone. The spacecraft must remain in this region
    c_cone = [p[2,k] >= alpha * cp.norm(p[:2,k], 2) for k in range(K)]
    # Spacecraft dynamics constraints
    c_vel = [v[:,k+1] == v[:,k] + h/m*f[:,k] - h*g*e3 for k in range(K-1)]
    c_pos = [p[:,k+1] == p[:,k] + h/2*(v[:,k] + v[:,k+1]) for k in range(K-1)]

    constraints = c_init + c_end + c_fmax + c_cone + c_vel + c_pos
    prob = cp.Problem(objective, constraints)
    res = prob.solve(verbose=False)


    cons = [c_init, c_end, c_fmax, c_cone, c_vel, c_pos]
    names = ['init', 'final', 'max thrust', 'trajectory cone', 'velocity dynamics', 'position dynamics']

    duals = {}
    for name, con in zip(names, cons):
        duals[name] = np.array([c.dual_value for c in con])

    return prob.status, (p.value, v.value, f.value), duals, res

def main():
    status, (p, v, f), duals, res = optimize_trajectory()

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    X = np.linspace(-40, 55, num=30)
    Y = np.linspace(-40, 55, num=30)
    X, Y = np.meshgrid(X, Y)
    alpha = 0.5
    Z = alpha*np.sqrt(X**2+Y**2)
    ax.plot(xs=p[0,:],ys=p[1,:],zs=p[2,:])
    # ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.viridis, linewidth=0, antialiased=True, alpha=0.7)
    ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.Blues, linewidth=0, antialiased=True, alpha=0.5)
    # ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.autumn, linewidth=0, antialiased=True, alpha=0.5)
    ax.quiver(p[0,:], p[1,:], p[2,:], f[0,:], f[1,:], f[2,:], color='k', antialiased=True, linewidth=0.7)

    ax.set_xlabel('x'); ax.set_ylabel('y'); ax.set_zlabel('z')
    ax.view_init(30, -120)
    # ax.view_init(30, 60)
    plt.savefig('traj.pdf', bbox_inches='tight')
    plt.show()
    plt.close()

    return

    # Multi trajectory plot, find minimal time trajectory
    traj = []
    time = []
    fuel = []
    for K in [55, 45, 35, 26, 25]:
        status, (p, v, f), duals, res = optimize_trajectory(K)
        print('K={} {}'.format(K, status))
        if (status != 'optimal'):
            break
        traj += [p]
        time += [K]
        fuel += [res]
        print('Time {}s  fuel {:.2f}'.format(K, res))

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    X = np.linspace(-40, 55, num=30)
    Y = np.linspace(-40, 55, num=30)
    X, Y = np.meshgrid(X, Y)
    alpha = 0.5
    Z = alpha*np.sqrt(X**2+Y**2)
    ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.Blues, linewidth=0)
    for i, (p, K) in enumerate(zip(traj, time)):
        ax.plot(xs=p[0,:],ys=p[1,:],zs=p[2,:], label='time {}s'.format(K))
    plt.legend()
    ax.set_xlabel('x'); ax.set_ylabel('y'); ax.set_zlabel('z')
    ax.view_init(30, -120)

    plt.savefig('traj_multi.pdf', bbox_inches='tight')
    plt.show()
    plt.close()

if __name__ == '__main__':
    main()
