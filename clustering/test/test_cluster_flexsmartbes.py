__author__ = 'Annika Wierichs'

from clustering.cluster import Cluster
from city.database import DataBase
from building.environment import Environment
from time import *
import os
import os


lt = localtime()
dirResults = "_results_clustering_multiDSync/{}-{:02d}-{:02d}_{:02d}-{:02d}".format(lt[0], lt[1], lt[2], lt[3], lt[4])
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

starting = 130
horizon = 86400
interval = 86400
stepSize = 1800
shareOfRenewables = 20
fromTime = starting * horizon
toTime = fromTime + horizon - stepSize
env = Environment(shareOfRenewables, stepSize)

listBes = DataBase.createRandomFlexSmartBuildings(10, stepSize, True, randomSeed=17, solPoolIntensity=4)
for b in range(len(listBes)):
    listBes[b].calcSchedulePool(fromTime, toTime)

# create list of differently sized clusters
clusterList = list()
for s in range(2):
    clusterList.append(Cluster(dirAbsResults, env, horizon, stepSize, interval))    # create clusters

for b in range(len(listBes)):
    clusterList[b%2].addMember(listBes[b])



# clusterList[0].chooseSchedules(fromTime)
# print "SOC in cl before:", clusterList[0].listBes[1].getSOC()
# clusterList[0].listBes[1].setSOC(1)
# print "SOC in list after:", listBes[2].getSOC()


