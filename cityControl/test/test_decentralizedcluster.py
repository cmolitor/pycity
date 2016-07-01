__author__ = 'Annika Wierichs'

from buildingControl.smartbes import SmartBes
from building.pvsystem import PVSystem
from city.database import DataBase
from cityControl.decentralizedcluster import DecentralizedCluster
from time import *
import os
import sys
from building.environment import Environment

# set values

stepSize = 900
horizon = 86400 * 2
interval = 86400
rsc = 3
startingH = 100

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
clusterTest = DecentralizedCluster(dirAbsResults, env, horizon, stepSize, interval)

listBESs = DataBase.createRandomBESs(10, (40,40), env, stepSize, rsc, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4, pseudorandom=True, randomSeed=2)

for bes in listBESs:
    clusterTest.addMember(bes)

# EXECUTE IDA, SIDA OR PIDA HERE !!!
perf, messages = clusterTest.IDA(fromTime)

print("\n\nPerformance (Interval):", perf)
print("Messages:", messages)
