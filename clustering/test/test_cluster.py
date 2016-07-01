__author__ = 'Annika Wierichs'

from clustering.smartbes import SmartBes
from city.cluster import Cluster
from city.database import DataBase
from time import *
import os
from building.environment import Environment

# set values

stepSize = 3600
horizon = 86400
interval = 86400
interval = 86400
noBes = 20

# create folder for simulation results
lt = localtime()
dirResults = "_results_test_cluster/{}-{:02d}-{:02d}_{:02d}-{:02d}_MIP_clustersize".format(lt[0], lt[1], lt[2], lt[3], lt[4])
if not os.path.exists(dirResults):
    os.makedirs(dirResults)
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

environment1 = Environment(20, stepSize)
cluster1 = Cluster(dirAbsResults, environment1, horizon, stepSize, interval)

# create smartbes objects (some for starters). add them to cluster
allBesList = DataBase.createRandomBuildings(noBes, stepSize, pseudorandom=True)

for d in range(120, 150):
    fromTime = d * horizon
    toTime = fromTime + horizon - stepSize
    for b in range(noBes):
        allBesList[b].calcSchedulePool(fromTime, toTime, objectiveFcn=1, absGap=2, relGap=0.2, solutionPoolIntensity=4)
        allBesList[b].calcFlexibility()
        cluster1.addMember(allBesList[b])

    performance = cluster1.chooseSchedules(fromTime, 'energy')

    print "\n\nPerformance: ", performance
