__author__ = 'Annika Wierichs'

from clustering.cluster import Cluster
from city.database import DataBase
from building.environment import Environment
from time import *

import os
import numpy as np
import random
import multiprocessing as mp


# basic data for simulation
# -------------------------

clusterSize_members = [5, 10, 15, 20, 25, 30, 40, 50]       # members in cluster
stepSize = 1800
startingHorizon = 0
noHorizons = 365
criterion = 'energy'

absGapSolutionPool = 2
seedForRandom = 3

horizon = 86400
interval = 86400
shareOfRenewables = 100  # 50% ?
solutionPoolIntensity = 4

includeDebuggingInfo = True
includeExecutionTimeLog = True


# set up other information etc
# ----------------------------

steps = horizon/stepSize
noOfClusterSplittings = len(clusterSize_members)

# container for performance-results of each cluster-splitting and each time step:
randomPerformances = np.zeros([noHorizons, noOfClusterSplittings])


# logging
# -------

lt = localtime()
scenario_name = "performancesRandomSchedules_{}ClS_{}Days_Start{}-".format(noOfClusterSplittings, noHorizons, startingHorizon)
dirResults = "_results_clustering_randomSchedules/{}-{:02d}-{:02d}_{:02d}-{:02d}".format(lt[0], lt[1], lt[2], lt[3], lt[4])
if not os.path.exists(dirResults):
    os.makedirs(dirResults)
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

# create folder and file for log files etc.
logfile_name = dirResults + "/logfile_Simulation.txt"
logfile = open(logfile_name, "a")
logfile.write("Simulation data:\n\nCluster sizes (members): {}\nStep Size: {}\nStarting Horizon: {}\nNo. of Horizons: {}\nCriterion: {}\nSolution Pool Gap: {}\nRandom-seed: {}\nShare of Renewables: {}\nSolution Pool Intensity: {}\n\n".format(clusterSize_members, stepSize, startingHorizon,
                                                                                                                                                                                                                                            noHorizons, criterion,
                                                                                                                                                                                                                                            absGapSolutionPool, seedForRandom,
                                                                                                                                                                                                                                            shareOfRenewables, solutionPoolIntensity))
logfile.close()

# create environment & cluster that generates and holds all FlexSmartBES objects
env = Environment(shareOfRenewables, stepSize)
allBesList = DataBase.createRandomFlexSmartBuildings(max(clusterSize_members), stepSize=stepSize, pseudorandom=True, randomSeed=seedForRandom, solPoolAbsGap=absGapSolutionPool, solPoolIntensity=solutionPoolIntensity)
# create list of differently sized clusters
clusterList = list()
for s in range(noOfClusterSplittings):
    clusterList.append(Cluster(dirAbsResults, env, horizon, stepSize, interval))    # create clusters
# assign BESs to clusters
for s in range(noOfClusterSplittings):
    for b in range(clusterSize_members[s]):
        clusterList[s].addMember(allBesList[b])


########################################################################################################################


# MAIN LOOP
# ---------
if includeExecutionTimeLog:
    startTimeMainloop = time()


for h in range(startingHorizon, startingHorizon + noHorizons):

    if includeExecutionTimeLog:
        startTimeDay = time()
    # basic variables
    fromTime = h * horizon
    toTime = fromTime + horizon - stepSize
    toTimeInterval = fromTime + interval - stepSize    # todo: needed?

    # calculate schedules for all available BESs
    for b in range(len(allBesList)):
        allBesList[b].calcSchedulePool(fromTime=fromTime, toTimeH=toTime)

    if includeExecutionTimeLog:
        logfile = open(logfile_name, "a")

########################################################################################################################

    # loop through different sizes of clusters
    for s in range(noOfClusterSplittings):

        if includeExecutionTimeLog:
            startTimeClSplitting = time()


        ################################################################################################################
        # CHOOSE SCHEDULES

        exec_time = 0
        if includeExecutionTimeLog:
            startTimeCluster = time()

        # random schedules
        randomPerformances[h-startingHorizon, s] = clusterList[s].chooseSchedulesRandomly(fromTime, criterion)

        print "Random:", randomPerformances[h-startingHorizon, s]   # for debugging

        if includeExecutionTimeLog:
            exec_time = time() - startTimeCluster
            logfile.write("\n\t\t\t--- {:.1f} members in cluster): {:.2f} s ---".format(clusterSize_members[s], exec_time))

    if includeExecutionTimeLog:
        logfile.write("\n\n\t\t--- Executing this day (day {}): {:.2f} s".format(h, time()-startTimeDay))
        logfile.close()

    # save arrays after each day as a backup
    np.save("{}/{}_h-{}.npy".format(dirResults, scenario_name, h), randomPerformances)

