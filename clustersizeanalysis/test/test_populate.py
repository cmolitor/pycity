#!/usr/bin/python

import cplex

# Model
c = cplex.Cplex()
# c.parameters.mip.pool.intensity.Cap = 5

# Set an overall node limit
# c.parameters.mip.limits.nodes.set(5000)

c.objective.set_sense(c.objective.sense.minimize)

# py-variables
# ------------

demandThermal = [0,     # -> first relevant element in t=1
                 14478691.79, 14596766.09, 14605507.87, 14546721.87, 14471099.61, 14353297.41, 14285812.57, 14291072.95,
                 14277490.78, 13937422.29, 13742817.42, 13586084.23, 13043376.87, 12595388.43, 12560229.09, 12882910.01,
                 13622245.72, 13764017.91, 13932222.79, 14058808.89, 14067549.8, 14025412.07, 14050797.88, 13966667.22]
                                    # thermal power demand each hour
horizon = 24                        # number of hours
TSLength = 3600                     # 3600 secs in 1 hour
rangeHorizon = range(1, horizon+1)  # hour array
rangeHorizon2 = range(0, horizon+1)  # dummy
modLevels = 1                       # number of modulation levels available
modLvlIni = 0                       # modulation level ini
HSThermalNominalPower = 10000       # power P_n (48100?)
# COP = 0.8                         # coefficient of performance
storageCapThermal = 450281000       # storage capacity
SoCini = 0.220772
SoCmin = 0.1                        # state of Charge min
SoCmax = 0.85                       # state of Charge min
noOfSolutions = 3                   # number of optimal solutions that will be returned

# variables
# ---------

# modulation level: on=1, off=0
MODLVL = []
for s in rangeHorizon2:
    MODLVLName = "MODLVL_"+str(s)
    MODLVL.append(MODLVLName)
c.variables.add(obj = [0] * len(MODLVL), names = MODLVL,
                lb = [0] * len(MODLVL), ub = [modLevels] * len(MODLVL),
                types = [c.variables.type.integer] * len(MODLVL))

# stored thermal energy
ETHStorage = []
for s in rangeHorizon2:
    ETHStorageName = "ETHStorage_"+str(s)
    ETHStorage.append(ETHStorageName)
c.variables.add(obj = [0] * len(ETHStorage), names = ETHStorage,
                lb = [SoCmin*storageCapThermal] * len(ETHStorage), ub = [SoCmax*storageCapThermal] * len(ETHStorage),
                types = [c.variables.type.continuous] * len(ETHStorage))

# power flow into storage at time=s
PTHStorage = []
for s in rangeHorizon2:
    PTHStorageName = "PTHStorage_"+str(s)
    PTHStorage.append(PTHStorageName)
c.variables.add(obj = [0] * len(PTHStorage), names = PTHStorage,
                lb = [-max(demandThermal[1:])/TSLength] * len(PTHStorage), ub = [HSThermalNominalPower] * len(PTHStorage),
                types = [c.variables.type.continuous] * len(PTHStorage))

# switch device on or off? on = 1, off = -1, no change = 0
switchOnOrOff = []
for s in rangeHorizon2:
    switchOnOrOffName = "switchOnOrOff_"+str(s)
    switchOnOrOff.append(switchOnOrOffName)
c.variables.add(obj = [0] * len(switchOnOrOff), names = switchOnOrOff,
                lb = [-1] * len(switchOnOrOff), ub = [1] * len(switchOnOrOff),
                types = [c.variables.type.integer] * len(switchOnOrOff))

# abs of switchOnOrOff (dummy)
abs_switchOnOrOff = []
for s in rangeHorizon2:
    abs_switchOnOrOffName = "abs_switchOnOrOff_"+str(s)
    abs_switchOnOrOff.append(abs_switchOnOrOffName)
c.variables.add(obj = [1] * len(abs_switchOnOrOff), names = abs_switchOnOrOff,
                lb = [0] * len(abs_switchOnOrOff), ub = [1] * len(abs_switchOnOrOff),
                types = [c.variables.type.integer] * len(abs_switchOnOrOff))

# switchSum = ["switch_Sum"]
# c.variables.add(obj = [1], names = switchSum, ub = [2],
                # types = [c.variables.type.integer])


# constraints
# -----------

for t in rangeHorizon:
    # dummy for switch & abs_switch
    thevars = [abs_switchOnOrOff[t], switchOnOrOff[t]]
    c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, -1])],
                             senses = ["G"], rhs = [-0.1])
    c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, 1])],
                             senses = ["G"], rhs = [-0.1])

    # # abs quadratic function: abs = sw^2
    # l = cplex.SparsePair([abs_switchOnOrOff[t]], val = [-1])					# -1 * abs
    # q = cplex.SparseTriple([switchOnOrOff[t]], [switchOnOrOff[t]], val = [1])	# 1 * sw^2
    # c.quadratic_constraints.add(lin_expr = l,
    #                             quad_expr = q,
    #                             sense = ["E"],
    #                             rhs = [0]) # names = ["absswtch_" + str(t)]

    # sync switch and MODLVL
    thevars = [switchOnOrOff[t], MODLVL[t], MODLVL[t-1]]
    c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1,-1, 1])],
                             senses = ["E"], rhs = [0], names = ["swtch_" + str(t)])
    # SoCmin <= energy in storage <= SoCmax
    thevars = [ETHStorage[t]]
    c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                             senses = ["G"], rhs = [SoCmin*storageCapThermal-1])
    c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                             senses = ["L"], rhs = [SoCmax*storageCapThermal+1])
    # energy in storage at time t = energy at time (t-1) + (TSLength * PTHStorage[t])
    thevars = [ETHStorage[t], ETHStorage[t-1], PTHStorage[t]]
    c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1,-1,-TSLength])],
                             senses = ["E"], rhs = [0])
    # energy from grid = energy stored + energy used
    thevars = [MODLVL[t], PTHStorage[t]]
    c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [HSThermalNominalPower * TSLength,-TSLength])],
                             senses = ["E"], rhs = [demandThermal[t]])

# MODLVL at t=0 = MODLVLini
thevars = [MODLVL[0]]
c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                         senses = ["E"], rhs = [modLvlIni])
# energy in storage at t=0 =  SoCini * storageCapThermal
thevars = [ETHStorage[0]]
c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                         senses = ["E"], rhs = [SoCini * storageCapThermal])

# sum of state switches
# sumCoeffs = [1]*horizon
# sumCoeffs.append(-1)
# thevars = []
# for i in rangeHorizon:
    # thevars.append(abs_switchOnOrOff[i])
# thevars.append(switchSum[0])
# c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, sumCoeffs)], senses = ["E"], rhs = [0])


# solve problem (1 solution)
# --------------------------

# c.solve()
# sol = c.solution

# # print solution


# if sol.is_primal_feasible():
#     print "Solution value  = ", sol.get_objective_value()
#     print "Fahrplan:"
#     for i in rangeHorizon:
#         print '%.0f \t' % sol.get_values(MODLVL[i]),
#     print ""
#     for i in rangeHorizon:
#         print '%.0f \t' % sol.get_values(switchOnOrOff[i]),
#     print ""
#     for i in rangeHorizon:
#         print '%.0f \t' % sol.get_values(abs_switchOnOrOff[i]),
# else:
#     print "No solution available."


# solve problem (solution pool)
# -----------------------------

c.parameters.mip.pool.absgap.set(1.0)
pool = c.populate_solution_pool()
noSol = c.solution.pool.get_num()

# print solution pool
print "Solutions (Number: %d)" % noSol
for n in range(noSol):
    print""
    for j in rangeHorizon:
        lvl = c.solution.pool.get_values(n, MODLVL[j])
        print '%.0f' % abs(lvl),
    print ""
    for j in rangeHorizon:
        _abs = c.solution.pool.get_values(n, abs_switchOnOrOff[j])
        print '%.0f' % abs(_abs),
    print ""

