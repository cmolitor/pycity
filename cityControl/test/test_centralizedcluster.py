__author__ = 'Annika Wierichs'

from buildingControl.smartbes import SmartBes
from building.pvsystem import PVSystem
from city.database import DataBase
from cityControl.centralizedcluster import CentralizedCluster
from time import *
import os
import sys
from building.environment import Environment

# set values

stepSize = 900
horizon = 86400 * 2
interval = 86400
rsc = 3
startingH = 125

fromTime = startingH * horizon
toTime = fromTime + horizon - stepSize

# create folder for simulation results
lt = localtime()
dirResults = "_results_test_cluster/{}-{:02d}-{:02d}_{:02d}-{:02d}_MIP_clustersize".format(lt[0], lt[1], lt[2], lt[3], lt[4])
if not os.path.exists(dirResults):
    os.makedirs(dirResults)
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

env = Environment(50, stepSize)
#print("env.sharePV: ", env.sharePV)
clusterTest = CentralizedCluster(dirAbsResults, env, horizon, stepSize, interval)

# create smartbes objects (some for starters). add them to cluster
# clusterTest.addMember(SmartBes(stepSize=stepSize, TER1= 2.3, TER2= 0, RSC=3.0, sizingMethod=-1, iApartments=1, sqm=150,
#                                    specDemandTh=166, env=env, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4))
# clusterTest.addMember(SmartBes(stepSize=stepSize, TER1=-2.3, TER2=-1, RSC=3.0, sizingMethod=-2, iApartments=3, sqm=100,
#                                    specDemandTh=130, env=env, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4))
#
# clusterTest.addMember(SmartBes(stepSize=stepSize, TER1= 2.3, TER2= 0, RSC=3.0, sizingMethod=-1, iApartments=1, sqm=150,
#                                    specDemandTh=166, env=env, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4))
# clusterTest.addMember(SmartBes(stepSize=stepSize, TER1=-2.3, TER2=-1, RSC=3.0, sizingMethod=-2, iApartments=3, sqm=100,
#                                    specDemandTh=130, env=env, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4))
#
# clusterTest.addMember(SmartBes(stepSize=stepSize, TER1=0, TER2=0, RSC=3.0, sizingMethod=1, iApartments=3, sqm=100,
#                                    specDemandTh=130, env=env, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4))
#
# pv = clusterTest.getBESs('primary')
# pv[2].addPVSystem(PVSystem(env, 4000))
# pv[3].addPVSystem(PVSystem(env, 6000))


listBESs = DataBase.createRandomBESs(10, (40,40), env, stepSize, rsc, solPoolAbsGap=2, solPoolRelGap=0.3, solPoolIntensity=4, pseudorandom=True, randomSeed=2)

print("listBESs: ",len(listBESs))
for bes in listBESs:
    clusterTest.addMember(bes)

perf = clusterTest.calcSchedules(fromTime, globalCoordination=True, localOptimization=True)

for bes in clusterTest.listBes:
    print "ObjFcn:", bes.getObjFcn(), "\nP_nom 1:", bes.getNominalElectricalPower1()
    if bes.PVSystem is not None:
        print "\twith PVSystem"
    for t in range(len(bes.getSchedule())):
        print '%.0f' % abs(bes.getSchedule()[t]),
        sys.stdout.softspace = 0
    print "(Globally optimal)"
    for t in range(len(bes.getLocallyOptimalSchedule())):
        print '%.0f' % abs(bes.getLocallyOptimalSchedule()[t]),
        sys.stdout.softspace = 0
    print "(Locally optimal)\n"

print "Performance:", perf
