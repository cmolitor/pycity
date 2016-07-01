__author__ = 'Christoph Molitor'

from time import *
import os
from building.environment import Environment
from clustersizeanalysis.cluster_cplex import Cluster
from building.bes import Bes



stepSize = 3600  # todo: not tested with other stepsize
startTime = 0  # 1814400
endTime = startTime + 86400 * 2
horizon = 86400*1  # horizon for scheduling
interval = 86400  # interval for scheduling

environment1 = Environment(100, stepSize)

TER1 = 2.32  # > 0: CHP; < 0: HP
TER2 = 0.0
RSC = 3.0
iApartments = 1
sqm = 146.0
specDemandTh = 166.0
configurationHS = "Bivalent"

# Sizing of electro-thermal heating system:
sizingMethod_CHP = -1  # MRM
sizingMethod_HP = -2

nBES = 1

# create folder for simulation results
lt = localtime()
scenario_name = "{}{:02d}{:02d}-{:02d}{:02d}_{}_RES-{}_RSC-{}_Hrzn-{}".format(lt[0], lt[1], lt[2], lt[3], lt[4], configurationHS, environment1.getShareRES(), RSC, float(horizon)/interval)
dirResults = "_results_LP/{}".format(scenario_name)
if not os.path.exists(dirResults):
    os.makedirs(dirResults)

dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

cluster1 = Cluster(dirAbsResults, environment1, horizon, stepSize, interval)

for b in range(1, 1+nBES, 1):
    bes1 = Bes(stepSize, TER1, TER2, RSC, sizingMethod_CHP, iApartments, sqm, specDemandTh, environment1)
    bes1.setMinRuntime1(7200.0)
    print("BES annual thermal demand: ", bes1.getAnnualThermalDemand())
    print("BES nominal thermal power of HS1: ", bes1.getNominalThermalPower1())
    print("BES nominal thermal power of HS2: ", bes1.getNominalThermalPower2())
    print("BES nominal electrical power of HS1: ", bes1.getNominalElectricalPower1())
    print("BES Thermal Power Curve: ", bes1.getThermalPower1(0, 86400))
    print("BES storage capacity: ", bes1.getStorageCapacity())
    # bes1.pthnom2 = -3000
    cluster1.addMember(bes1)

print("Number of BES: {}".format(cluster1.getNumberOfMembers()))
cluster1.setSurchargeLoad(0)
# print("Demand Curve: {}".format(cluster1.getElectricalDemandCurve(startTime, endTime)))
print("Annual Electricity Demand: {}".format(cluster1.getAnnualElectricityConsumption(0)))
# print("RES Curve: {}".format(cluster1.getRenewableGenerationCurve(startTime, endTime)))
# print("Fluc Curve: {}".format(cluster1.getFluctuationsCurve(startTime, endTime)))

cluster1.setTypeOptimization("MIP")

for time in range(startTime, endTime, interval):
    (ratioMaxEnergy, ratioMaxPower, relGap, avgRemainder, avgFluctuations) = cluster1.calcSchedules(time)
    print("ratioMaxFluc: {}".format(ratioMaxEnergy))
    print("ratioMaxPower: {}".format(ratioMaxPower))
    print("Gap: {}".format(relGap))  # gap >= 0: real gap value; gap == -1: optimal solution found during presolve; gap == -2: Relaxations
    print("avgRemainder: {}".format(avgRemainder))
    print("avgFluctuations: {}".format(avgFluctuations))