__author__ = 'Sonja Kolen'

# this file is intended to execute multiple simulation runs with different configurations of the simulation

from simulation import simulation
import subprocess

# (stepsize, sim_days, interval, RES_ratio, extend_neighborhood, el_radius, excl_gasboilers, solpoolint, absgap, act_msg_log, bivalent_HS, algtype, criterion_type)

#15min step: multicast-based coordination 25% RES mono, abs gap 0 - 7, 14 days
#simulation(stepsize=900, sim_days=14, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=0, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=14, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=1, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=14, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=14, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=3, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=14, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=4, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=14, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=5, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=14, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=6, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=14, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=7, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')

#15min step: tree-based coordination 0%, 25%, 50%, 75%, 100% RES mono
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=0, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='tree', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='tree', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=50, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='tree', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=75, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='tree', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=100, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='tree', criterion_type='maxmindiff')

#15min step: tree-based coordination 25% RES bivalent
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=1, algtype='tree', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=75, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=1, algtype='tree', criterion_type='maxmindiff')


#15min step: multicast-based coordination 0%, 25%, 50%, 75%, 100% RES mono
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=0, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
simulation(stepsize=900, sim_days=2, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='tree', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=50, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=75, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=100, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='multicast', criterion_type='maxmindiff')

#15min step:  multicast-based coordination 25% RES bivalent
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=1, algtype='multicast', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=75, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=1, algtype='multicast', criterion_type='maxmindiff')


#15min step: uncoordinated schedule selection 0%, 25%, 50%, 75%, 100% RES mono + bivalent
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=0, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='uncoord', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='uncoord', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=50, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='uncoord', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=75, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='uncoord', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=100, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=0, algtype='uncoord', criterion_type='maxmindiff')

#15min step: uncoordinated schedule selection 25% RES bivalent
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=25, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=1, algtype='uncoord', criterion_type='maxmindiff')
#simulation(stepsize=900, sim_days=365, interval=86400, RES_ratio=75, extend_neighborhood=0, el_radius=20, excl_gasboilers=1, solpoolint=3, absgap=2, act_msg_log=0, bivalent_HS=1, algtype='uncoord', criterion_type='maxmindiff')