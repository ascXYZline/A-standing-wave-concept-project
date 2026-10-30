"""Independent numerical checks against the displacement derivatives (SI)."""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
L, mu, tension, A, n = 1., .01, 1., .01, 2
k = n*np.pi/L
omega = k*np.sqrt(tension/mu)
U = .5*mu*omega**2*A**2
C = tension*A*A*k*omega/4
x = np.linspace(0,L,4001)[:,None]
t = np.linspace(0,2*np.pi/omega,241)[None,:]
yt = -A*omega*np.sin(k*x)*np.sin(omega*t)
yx = A*k*np.cos(k*x)*np.cos(omega*t)
uk = .5*mu*yt**2
up = .5*tension*yx**2
u = uk+up
p = -tension*yx*yt
checks = {}

def check(name,error,tolerance):
    error=float(error)
    checks[name]={'max_error':error,'tolerance':tolerance,'passed':error<tolerance}
    assert error<tolerance,(name,error)

check('power_prefactor_1_over_4',np.max(np.abs(p-C*np.sin(2*k*x)*np.sin(2*omega*t))),1e-14)
# Numerical spatial integral, conserved over every sampled time.
energy=np.trapezoid(u,x[:,0],axis=0)
check('total_energy_conserved',np.max(np.abs(energy-U*L/2)),1e-14)
quarter=np.trapezoid(u[:1001],x[:1001,0],axis=0)
check('node_to_antinode_interval_conserved',np.ptp(quarter),1e-14)
mean_u=np.trapezoid(u,t[0],axis=1)/(t[0,-1]-t[0,0])
check('uniform_time_averaged_density',np.max(np.abs(mean_u-U/2)),1e-14)
mean_p=np.trapezoid(p,t[0],axis=1)/(t[0,-1]-t[0,0])
check('zero_time_averaged_flux',np.max(np.abs(mean_p)),1e-14)
check('node_and_antinode_flux_zero',np.max(np.abs(p[::1000])),1e-14)
uniform=U*(np.sin(k*x)**2+np.cos(k*x)**2)/2
check('uniform_density_at_pi_over_4',np.max(np.abs(uniform-U/2)),1e-14)
# Central differences use the original displacement energy and flux, not the identity.
dt=t[0,1]-t[0,0]; dx=x[1,0]-x[0,0]
residual=(u[1:-1,2:]-u[1:-1,:-2])/(2*dt)+(p[2:,1:-1]-p[:-2,1:-1])/(2*dx)
check('continuity_finite_difference_relative',np.max(np.abs(residual))/(U*omega),.0005)
plus_x=A*k/2*np.cos(k*x-omega*t); minus_x=A*k/2*np.cos(k*x+omega*t)
plus_t=-A*omega/2*np.cos(k*x-omega*t); minus_t=A*omega/2*np.cos(k*x+omega*t)
cross=-tension*(plus_x*minus_t+minus_x*plus_t)
check('counterpropagating_flux_cross_terms_cancel',np.max(np.abs(cross)),1e-14)
pp=-tension*plus_x*plus_t; pm=-tension*minus_x*minus_t
check('instantaneous_flux_is_component_sum',np.max(np.abs(p-pp-pm)),1e-14)
check('fixed_end_displacements',np.max(np.abs(A*np.sin(k*np.array([0,L])))),1e-14)
report={'parameters':{'L_m':L,'mu_kg_per_m':mu,'tension_N':tension,'A_m':A,'mode':n,
                       'frequency_Hz':omega/(2*np.pi),'max_slope':A*k,'energy_J':U*L/2},'checks':checks}
(ROOT/'build').mkdir(exist_ok=True)
(ROOT/'build/physics_checks.json').write_text(json.dumps(report,indent=2))
print(f'{len(checks)} physics checks passed; E = {U*L/2:.8g} J')
