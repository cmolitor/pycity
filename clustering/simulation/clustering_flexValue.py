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

noBes = 480
stepSize = 1800
startingHorizon = 273
noHorizons = 92
criterion = 'energy'

absGapSolutionPool = 2
seedForRandom = 17

minNoOfClusters = 7
maxNoOfClusters = 20
stepSizeOfClusterSplitting = 5
clusteringArray = [15, 20, 30, 60]      # set to [] to use the above options!

#  32, 24, 16, 08 members for 480
# [15, 20, 30, 60]

#  30, 25, 20, 15, 10,7.5, 5 members for 300
# [10, 12, 15, 20, 30, 40, 60]

#  50, 40, 30, 25, 20, 15, 10 members for 500
# [10, 13, 17, 20, 25, 33, 50]

horizon = 86400
interval = 86400
shareOfRenewables = 20
solutionPoolIntensity = 4
includeDebuggingInfo = True
includeExecutionTimeLog = True
parallelizeLinux = False


# for parallelization:
def chooseSchedulesHelper(resultList, c, _cluster, fromTime, criterion):
    result = _cluster.chooseSchedules(fromTime, criterion)
    resultList[c] = result



# set up other information etc
# ----------------------------

steps = horizon/stepSize

if clusteringArray is []:
    clusteringArray = range(minNoOfClusters, maxNoOfClusters+1, stepSizeOfClusterSplitting)  # +1 so this last number will be included
else:
    minNoOfClusters = clusteringArray[0]
    maxNoOfClusters = clusteringArray[-1]

noOfClusterSplittings = len(clusteringArray)

# container for performance-results of each cluster-splitting and each time step:
performances = np.zeros([2, noHorizons, noOfClusterSplittings, maxNoOfClusters])
overallPerformances = np.zeros([2, noHorizons, noOfClusterSplittings])

SOCs = np.zeros([2, noOfClusterSplittings, noBes])

# create folder for simulation results etc.
lt = localtime()
scenario_name = "performances_{}BES_{}ClS_{}Days_Start{}-".format(noBes, noOfClusterSplittings, noHorizons, startingHorizon)
dirResults = "_results_clustering_flexValue/{}-{:02d}-{:02d}_{:02d}-{:02d}".format(lt[0], lt[1], lt[2], lt[3], lt[4])
if not os.path.exists(dirResults):
    os.makedirs(dirResults)
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

# create folder and file for log files etc.
logfile_name = dirResults + "/logfile_Simulation.txt"
logfile = open(logfile_name, "a")
logfile.write("Simulation data:\n\nNo. of Bes: {}\nStep Size: {}\nStarting Horizon: {}\nNo. of Horizons: {}\nCriterion: {}\nSolution Pool Gap: {}\nRandom-seed: {}\nCluster Splitting: {}\nShare of Renewables: {}\nSolution Pool Intensity: {}\n\n".format(noBes, stepSize, startingHorizon,
                                                                                                                                                                                                                                                            noHorizons, criterion,
                                                                                                                                                                                                                                                            absGapSolutionPool, seedForRandom,
                                                                                                                                                                                                                                                            clusteringArray, shareOfRenewables,
                                                                                                                                                                                                                                                            solutionPoolIntensity))
logfile.close()

# create environment & cluster that generates and holds all FlexSmartBES objects
env = Environment(shareOfRenewables, stepSize)
allBesList = DataBase.createRandomFlexSmartBuildings(noBes, stepSize=stepSize, pseudorandom=True, randomSeed=seedForRandom, solPoolAbsGap=absGapSolutionPool, solPoolIntensity=solutionPoolIntensity)


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
    toTimeInterval = fromTime + interval - stepSize    # todo: needed? CMO: yes, actually I think your implementation is only ok if you have horizon=86400

    if includeDebuggingInfo:
        logfile = open(logfile_name, "a")
        logfile.write("\n\n\nDay/Horizon: {}".format(h))

    # calculate schedules and impacts for all available BES's
    for b in range(noBes):
        allBesList[b].calcSchedulePool(fromTime=fromTime, toTimeH=toTime)
        allBesList[b].calcFlexibility()


########################################################################################################################


    # loop through different splittings of clusters
    for n_index, n in zip(range(noOfClusterSplittings), clusteringArray):    # +1 so this last number will be included
        if includeExecutionTimeLog:
            startTimeClSplitting = time()

        # for debugging
        if includeDebuggingInfo:
                logfile.write("\n\n\n\t{} CLUSTERS\t\tCluster Splitting No. {}\t\tAverage No. of BES per Cluster: {:.2f}\t\t(Day/Horizon: {})\n".format(n, n_index, float(noBes)/float(n), h))


        ################################################################################################################
        # clustering randomly

        # create n clusters, save clusters to a list and randomly add BES's to each of them
        random.seed(seedForRandom + h)  # for reproducibility (add h to vary clustering for each day)
        randomIndexes = random.sample(range(noBes), noBes)
        clusterListRandom = list()
        for c in range(n):
            clusterListRandom.append(Cluster(dirAbsResults, env, horizon, stepSize, interval))    # create clusters
        for b in range(noBes):
            clusterListRandom[b % n].addMember(allBesList[ randomIndexes[b] ])                    # randomly add BES's to clusters


        ################################################################################################################
        # CHOOSE SCHEDULES (R)

        # have members of clusters choose their best schedules according to chosen criterion
        # loop through all created clusters


        if parallelizeLinux:
            if includeExecutionTimeLog:
                exec_time = 0
                startTimeCluster = time()
            chooseSchedulesProcs = []
            manager = mp.Manager()
            resultList = manager.list(range(n))
            for c in range(n):
                proc = mp.Process(target=chooseSchedulesHelper, args=(resultList, c, clusterListRandom[c], fromTime, criterion))
                proc.start()
                chooseSchedulesProcs.append(proc)
            for p in range(len(chooseSchedulesProcs)):
                chooseSchedulesProcs[p].join()
            for c in range(n):
                performances[0, h-startingHorizon, n_index, c] = resultList[c]
            if includeExecutionTimeLog:
                exec_time = time() - startTimeCluster
                logfile.write("\n\t\t\t--- time choosing schedules (PARALLEL random clustering): ({:.1f} members): {:.2f} s ---".format(float(noBes)/float(n), exec_time))
        else:
            exec_time = 0
            if includeExecutionTimeLog:
                startTimeCluster = time()
            for c in range(n):
                performances[0, h-startingHorizon, n_index, c] = clusterListRandom[c].chooseSchedules(fromTime=fromTime, criterion=criterion)
            if includeExecutionTimeLog:
                exec_time = time() - startTimeCluster
                logfile.write("\n\t\t\t--- time choosing schedules (SERIAL random clustering): ({:.1f} members): {:.2f} s ---".format(float(noBes)/float(n), exec_time))


        greatestDiffOfTwoClustersR = max(performances[0, h-startingHorizon, n_index, 0:n]) - min(performances[0, h-startingHorizon, n_index, 0:n])
        medianPerformanceR = np.median(performances[0, h-startingHorizon, n_index, 0:n])                                                             # find median of performances
        compactnessPerformanceR = np.sum([(medianPerformanceR - performances[0, h-startingHorizon, n_index, c]) ** 2 for c in range(n)]) / n    # calculate average square error per cluster
        # # save states of charge since they will be changed again before new day
        # for b in range(len(allBesList)):
        #     SOCs[0, n_index, b] = allBesList[b].getSOC()


        ################################################################################################################
        # measure overall global performance

        flucCurve = np.zeros(horizon/stepSize)
        remCurve = np.zeros(horizon/stepSize)
        for c in range(n):
            flucCurve += clusterListRandom[c].getFluctuationsCurve(fromTime, toTime)
            remCurve += clusterListRandom[c].getRemainder()
        overallPerformances[0, h-startingHorizon, n_index] = Cluster.calcPerformanceMeasure(remCurve, flucCurve, criterion)

########################################################################################################################




        # --------------------------------------------------------------------------------------------------------------
        # now use flexibility value to possibly improve results
        # --------------------------------------------------------------------------------------------------------------




########################################################################################################################
        # clustering by distributing nominal power equally among clusters


        # create lists of CHP-BES and HP-BES.
        besListCHP = [b for b in allBesList if b.getTER1() > 0]       # CHP
        besListHP = [b for b in allBesList if b.getTER1() < 0]        # HP
        besListNoFlex = [b for b in allBesList if b.getTER1() == 0]   # no thermal storage
        # sort by NomPower for proper assignment to clusters later.
        besListCHP = sorted(besListCHP, key=lambda flexsmartbes: flexsmartbes.getNominalElectricalPower1())     # don't reverse since NomPower is negative
        besListHP = sorted(besListHP, key=lambda flexsmartbes: flexsmartbes.getNominalElectricalPower1(), reverse=True)

        # create specified number of clusters and save in clusterListFlex
        clusterListFlex = list()
        for i in range(n):
            clusterListFlex.append(Cluster(dirAbsResults, env, horizon, stepSize, interval))

        # assign BESs to clusters, so that Flex value will be similar for all clusters.
        # add BES in order of sorted list (starting with highest Flex*NomPower value), always adding BES to cluster with lowest accumulated NomPower value.

        # assign CHP-BES to clusters
        clusterPowerSumAbsCHP = np.zeros(n)
        for b in range(len(besListCHP)):
            clIndex = np.argmin(clusterPowerSumAbsCHP)  # add to the cluster currently accumulating lowest Flex*NomPower value
            clusterListFlex[clIndex].addMember(besListCHP[b])
            clusterPowerSumAbsCHP[clIndex] += abs(besListCHP[b].getNominalElectricalPower1())

        # assign HP-BES to clusters
        clusterPowerSumAbsHP = np.zeros(n)
        for b in range(len(besListHP)):
            clIndex = np.argmin(clusterPowerSumAbsHP)    # add to the cluster currently accumulating lowest Flex*NomPower value (max since values are negative for HPs)
            clusterListFlex[clIndex].addMember(besListHP[b])
            clusterPowerSumAbsHP[clIndex] += abs(besListHP[b].getNominalElectricalPower1())

        # equally assign GB-BES to clusters
        for b in range(len(besListNoFlex)):
            clusterListFlex[b % n].addMember(besListNoFlex[b])




########################################################################################################################
        # clustering by also distributing flexibility equally

        # save sum of flexibility of each CHP and HP BESs for each cluster
        clusterFlexHP = np.zeros(n)
        clusterFlexCHP = np.zeros(n)
        for c in range(n):
            clusterFlexCHP[c] = np.sum([clusterListFlex[c].listBesCHP[b].getFlexibility() for b in range(len(clusterListFlex[c].listBesCHP))])
            clusterFlexHP[c] = np.sum([clusterListFlex[c].listBesHP[b].getFlexibility() for b in range(len(clusterListFlex[c].listBesHP))])

        # find min and max of CHP / HP power accumulated in clusters and set to a 10 % tolerance
        minClusterPowerSumAbsCHP = min(clusterPowerSumAbsCHP)*0.8
        maxClusterPowerSumAbsCHP = max(clusterPowerSumAbsCHP)*1.2
        minClusterPowerSumAbsHP = min(clusterPowerSumAbsHP)*0.8
        maxClusterPowerSumAbsHP = max(clusterPowerSumAbsHP)*1.2
        # calculate average sum of flexibility per cluster
        avgFlexPerClusterCHP = sum(clusterFlexCHP) / n
        avgFlexPerClusterHP = sum(clusterFlexHP) / n
        # also calculate average sum of Nom. power per cluster
        avgPowerSumAbsPerClCHP = sum(clusterPowerSumAbsCHP) / n
        avgPowerSumAbsPerClHP = sum(clusterPowerSumAbsHP) / n

        # print "\n\n\nNEW SWITCHING PHASE (", n, "clusters)\n-------------------\n"

        # keep switching BESs between the clusters with highest and lowest flexibility

        # --------------------------------------------------------------------------------------------------------------
        # CHP

        # print "\n\n-----\n-CHP-\n-----\n\n"

        loopGuard = 0
        while(True):
            # find clusters with best and worst flexibility
            clIndexBest = np.argmax(clusterFlexCHP)
            clIndexWorst = np.argmin(clusterFlexCHP)
            # gap in flexibility between these two clusters
            gapInFlexBetweenBestAndWorstCl = clusterFlexCHP[clIndexBest] - clusterFlexCHP[clIndexWorst]
            # find ideal flexibility difference
            wantedFlexDiff = min(abs(avgFlexPerClusterCHP - clusterFlexCHP[clIndexWorst]), abs(avgFlexPerClusterCHP - clusterFlexCHP[clIndexBest]))

            # set up variables
            bw_best = 0
            bb_best = 0
            gapBest = float('inf')

            # go through all combinations of BESs from best and worst cluster
            for bb in range(len(clusterListFlex[clIndexBest].listBesCHP)):
                for bw in range(len(clusterListFlex[clIndexWorst].listBesCHP)):

                    availableFlexDiff = clusterListFlex[clIndexBest].listBesCHP[bb].getFlexibility() - clusterListFlex[clIndexWorst].listBesCHP[bw].getFlexibility()

                    # check if flexibility of best cluster's BES is greater than that of worst cluster's BES
                    if availableFlexDiff > 0:

                        # calculate new sums of power in clusters that would result from switching BESs
                        nomPowerBesWorstCl = abs(clusterListFlex[clIndexWorst].listBesCHP[bw].getNominalElectricalPower1())
                        nomPowerBesBestCl = abs(clusterListFlex[clIndexBest].listBesCHP[bb].getNominalElectricalPower1())
                        newPowerSumWorstCl = clusterPowerSumAbsCHP[clIndexWorst] - nomPowerBesWorstCl + nomPowerBesBestCl
                        newPowerSumBestCl = clusterPowerSumAbsCHP[clIndexBest] + nomPowerBesWorstCl - nomPowerBesBestCl

                        # check if switching these two BESs would cause one cluster to accumulate too much or too little nom. power
                        if minClusterPowerSumAbsCHP <= newPowerSumWorstCl <= maxClusterPowerSumAbsCHP and minClusterPowerSumAbsCHP <= newPowerSumBestCl <= maxClusterPowerSumAbsCHP:

                            gapBetweenWantedAndAvailableFlexDiff = abs(wantedFlexDiff - availableFlexDiff)

                            # check if switching BESs would be more gainful than previously found switching options
                            if gapBetweenWantedAndAvailableFlexDiff < gapBest and availableFlexDiff < gapInFlexBetweenBestAndWorstCl:
                                bw_best = bw
                                bb_best = bb
                                gapBest = gapBetweenWantedAndAvailableFlexDiff

                # also check if it is gainful to only move one BES from best cluster to worst cluster without replacing it by another BES

                availableFlexFromBestCluster = clusterListFlex[clIndexBest].listBesCHP[bb].getFlexibility()

                # calculate new sums of power in clusters that would result from switching BESs
                nomPowerBesBestCl = abs(clusterListFlex[clIndexBest].listBesCHP[bb].getNominalElectricalPower1())
                newPowerSumWorstCl = clusterPowerSumAbsCHP[clIndexWorst] + nomPowerBesBestCl
                newPowerSumBestCl = clusterPowerSumAbsCHP[clIndexBest] - nomPowerBesBestCl

                # check if switching these two BESs would cause one cluster to accumulate too much or too little nom. power
                if minClusterPowerSumAbsCHP <= newPowerSumWorstCl <= maxClusterPowerSumAbsCHP and minClusterPowerSumAbsCHP <= newPowerSumBestCl <= maxClusterPowerSumAbsCHP:

                    gapBetweenWantedAndAvailableFlexDiff = abs(wantedFlexDiff - availableFlexFromBestCluster)

                    # check if switching BESs would be more gainful than previously found switching options
                    if gapBetweenWantedAndAvailableFlexDiff < gapBest and availableFlexFromBestCluster < gapInFlexBetweenBestAndWorstCl:
                        bw_best = -1
                        bb_best = bb
                        gapBest = gapBetweenWantedAndAvailableFlexDiff


            # check if there are BESs that should be switched to distribute flexibility more equally
            if gapBest < float('inf'):
                # for debugging
                # if bw_best is not -1:
                    # print "Switch BES", bw_best+1, "(Cluster", clIndexWorst+1, ") and BES", bb_best+1, "(Cluster", clIndexBest+1, ")."
                # else:
                    # print "*** Move BES", bb_best+1, "(Cluster", clIndexBest+1, ") to Cluster", clIndexWorst+1, "***"
                # define BESs to be switched
                if bw_best is not -1:
                    besFromWorstCluster = clusterListFlex[clIndexWorst].listBesCHP[bw_best]     # BES from worst cluster
                besFromBestCluster = clusterListFlex[clIndexBest].listBesCHP[bb_best]           # BES from best cluster
                # switch chosen BESs
                if bw_best is not -1:
                    clusterListFlex[clIndexWorst].deleteMember(besFromWorstCluster)             # delete from worst cluster
                clusterListFlex[clIndexWorst].addMember(besFromBestCluster)                     # add to worst cluster
                clusterListFlex[clIndexBest].deleteMember(besFromBestCluster)                   # delete from worst cluster
                if bw_best is not -1:
                    clusterListFlex[clIndexBest].addMember(besFromWorstCluster)                 # add to worst cluster

                if bw_best is not -1:
                    # update sum of power for both clusters
                    clusterPowerSumAbsCHP[clIndexWorst] = clusterPowerSumAbsCHP[clIndexWorst] - abs(besFromWorstCluster.getNominalElectricalPower1()) + abs(besFromBestCluster.getNominalElectricalPower1())
                    clusterPowerSumAbsCHP[clIndexBest] = clusterPowerSumAbsCHP[clIndexBest] + abs(besFromWorstCluster.getNominalElectricalPower1()) - abs(besFromBestCluster.getNominalElectricalPower1())
                    # update sum of flexibility for both clusters
                    clusterFlexCHP[clIndexWorst] = clusterFlexCHP[clIndexWorst] - besFromWorstCluster.getFlexibility() + besFromBestCluster.getFlexibility()
                    clusterFlexCHP[clIndexBest] = clusterFlexCHP[clIndexBest] + besFromWorstCluster.getFlexibility() - besFromBestCluster.getFlexibility()
                else:
                    # update sum of power for both clusters
                    clusterPowerSumAbsCHP[clIndexWorst] = clusterPowerSumAbsCHP[clIndexWorst] + abs(besFromBestCluster.getNominalElectricalPower1())
                    clusterPowerSumAbsCHP[clIndexBest] = clusterPowerSumAbsCHP[clIndexBest] - abs(besFromBestCluster.getNominalElectricalPower1())
                    # update sum of flexibility for both clusters
                    clusterFlexCHP[clIndexWorst] = clusterFlexCHP[clIndexWorst] + besFromBestCluster.getFlexibility()
                    clusterFlexCHP[clIndexBest] = clusterFlexCHP[clIndexBest] - besFromBestCluster.getFlexibility()

            # break from switching loop, if there are no more CHPs to be moved
            else:
                break

            loopGuard += 1
            if loopGuard > 500:
                print "loop guard breaks from while in CHP switching."
                break

        # also make sure, that clusters have similar numbers of BESs
        numbersOfCHPsInClusters = [clusterListFlex[c].getNumberOfPrimaryHeaters("CHP") for c in range(n)]
        while float(max(numbersOfCHPsInClusters) - min(numbersOfCHPsInClusters)) / float(max(numbersOfCHPsInClusters)) >= float(1)/float(3):

            if max(numbersOfCHPsInClusters)-1 is min(numbersOfCHPsInClusters):
                break

            minIndices = [c for c in range(len(numbersOfCHPsInClusters)) if numbersOfCHPsInClusters[c] is min(numbersOfCHPsInClusters)]
            maxIndices = [c for c in range(len(numbersOfCHPsInClusters)) if numbersOfCHPsInClusters[c] is max(numbersOfCHPsInClusters)]
            minFlexibilities = [clusterFlexCHP[cb] for cb in minIndices]
            maxFlexibilities = [clusterFlexCHP[cg] for cg in maxIndices]

            if len(minIndices) > len(maxIndices):
                for s in range(len(maxIndices)):
                    maxClusterHighestFlexIndex = maxIndices[np.argmax(maxFlexibilities)]
                    maxClusterFlex = max(maxFlexibilities)
                    minClusterLowestFlexIndex = minIndices[np.argmin(minFlexibilities)]
                    maxFlexibilities[np.argmax(maxFlexibilities)] = 0
                    minFlexibilities[np.argmin(minFlexibilities)] = float('inf')

                    besIndexFromGoodCluster = np.argmin([abs(maxClusterFlex - BES.getFlexibility() - avgFlexPerClusterCHP) for BES in clusterListFlex[maxClusterHighestFlexIndex].listBesCHP])
                    besFromGoodCluster = clusterListFlex[maxClusterHighestFlexIndex].listBesCHP[besIndexFromGoodCluster]           # BES from best cluster

                    # print "+++ (CHP) Move excess BES", besIndexFromGoodCluster+1, "(Cluster", maxClusterHighestFlexIndex+1, ") to poor little Cluster", minClusterLowestFlexIndex+1, "+++"
                    # switch chosen BESs
                    clusterListFlex[minClusterLowestFlexIndex].addMember(besFromGoodCluster)                     # add to worst cluster
                    clusterListFlex[maxClusterHighestFlexIndex].deleteMember(besFromGoodCluster)                   # delete from worst cluster
                    # update sum of power for both clusters
                    clusterPowerSumAbsCHP[minClusterLowestFlexIndex] = clusterPowerSumAbsCHP[minClusterLowestFlexIndex] + abs(besFromGoodCluster.getNominalElectricalPower1())
                    clusterPowerSumAbsCHP[maxClusterHighestFlexIndex] = clusterPowerSumAbsCHP[maxClusterHighestFlexIndex] - abs(besFromGoodCluster.getNominalElectricalPower1())
                    # update sum of flexibility for both clusters
                    clusterFlexCHP[minClusterLowestFlexIndex] = clusterFlexCHP[minClusterLowestFlexIndex] + besFromGoodCluster.getFlexibility()
                    clusterFlexCHP[maxClusterHighestFlexIndex] = clusterFlexCHP[maxClusterHighestFlexIndex] - besFromGoodCluster.getFlexibility()
            else:
                for s in range(len(minIndices)):
                    maxClusterHighestFlexIndex = maxIndices[np.argmax(maxFlexibilities)]
                    maxClusterFlex = max(maxFlexibilities)
                    maxFlexibilities[np.argmax(maxFlexibilities)] = 0
                    minFlexibilities[np.argmin(minFlexibilities)] = float('inf')

                    besIndexFromGoodCluster = np.argmin([abs(maxClusterFlex - BES.getFlexibility() - avgFlexPerClusterCHP) for BES in clusterListFlex[maxClusterHighestFlexIndex].listBesCHP])
                    besFromGoodCluster = clusterListFlex[maxClusterHighestFlexIndex].listBesCHP[besIndexFromGoodCluster]           # BES from best cluster

                    # print "+++ (CHP) Move excess BES", besIndexFromGoodCluster+1, "(Cluster", maxClusterHighestFlexIndex+1, ") to poor little Cluster", minIndices[s]+1, "+++"
                    # switch chosen BESs
                    clusterListFlex[minIndices[s]].addMember(besFromGoodCluster)                     # add to worst cluster
                    clusterListFlex[maxClusterHighestFlexIndex].deleteMember(besFromGoodCluster)                   # delete from worst cluster
                    # update sum of power for both clusters
                    clusterPowerSumAbsCHP[minIndices[s]] = clusterPowerSumAbsCHP[minIndices[s]] + abs(besFromGoodCluster.getNominalElectricalPower1())
                    clusterPowerSumAbsCHP[maxClusterHighestFlexIndex] = clusterPowerSumAbsCHP[maxClusterHighestFlexIndex] - abs(besFromGoodCluster.getNominalElectricalPower1())
                    # update sum of flexibility for both clusters
                    clusterFlexCHP[minIndices[s]] = clusterFlexCHP[minIndices[s]] + besFromGoodCluster.getFlexibility()
                    clusterFlexCHP[maxClusterHighestFlexIndex] = clusterFlexCHP[maxClusterHighestFlexIndex] - besFromGoodCluster.getFlexibility()

            numbersOfCHPsInClusters = [clusterListFlex[c].getNumberOfPrimaryHeaters("CHP") for c in range(n)]




        # --------------------------------------------------------------------------------------------------------------
        # HP

        # print "\n\n----\n-HP-\n----\n\n"

        loopGuard = 0
        while(True):
            # find clusters with best and worst flexibility
            clIndexBest = np.argmax(clusterFlexHP)
            clIndexWorst = np.argmin(clusterFlexHP)
            # gap in flexibility between these two clusters
            gapInFlexBetweenBestAndWorstCl = clusterFlexHP[clIndexBest] - clusterFlexHP[clIndexWorst]
            # find ideal flexibility difference
            wantedFlexDiff = min(abs(avgFlexPerClusterHP - clusterFlexHP[clIndexWorst]), abs(avgFlexPerClusterHP - clusterFlexHP[clIndexBest]))

            # set up variables
            bw_best = 0
            bb_best = 0
            gapBest = float('inf')

            # go through all combinations of BESs from best and worst cluster
            for bb in range(len(clusterListFlex[clIndexBest].listBesHP)):
                for bw in range(len(clusterListFlex[clIndexWorst].listBesHP)):

                    availableFlexDiff = clusterListFlex[clIndexBest].listBesHP[bb].getFlexibility() - clusterListFlex[clIndexWorst].listBesHP[bw].getFlexibility()

                    # check if flexibility of best cluster's BES is greater than that of worst cluster's BES
                    if availableFlexDiff > 0:

                        # calculate new sums of power in clusters that would result from switching BESs
                        nomPowerBesWorstCl = abs(clusterListFlex[clIndexWorst].listBesHP[bw].getNominalElectricalPower1())
                        nomPowerBesBestCl = abs(clusterListFlex[clIndexBest].listBesHP[bb].getNominalElectricalPower1())
                        newPowerSumWorstCl = clusterPowerSumAbsHP[clIndexWorst] - nomPowerBesWorstCl + nomPowerBesBestCl
                        newPowerSumBestCl = clusterPowerSumAbsHP[clIndexBest] + nomPowerBesWorstCl - nomPowerBesBestCl

                        # check if switching these two BESs would cause one cluster to accumulate too much or too little nom. power
                        if minClusterPowerSumAbsHP <= newPowerSumWorstCl <= maxClusterPowerSumAbsHP and minClusterPowerSumAbsHP <= newPowerSumBestCl <= maxClusterPowerSumAbsHP:

                            gapBetweenWantedAndAvailableFlexDiff = abs(wantedFlexDiff - availableFlexDiff)

                            # check if switching BESs would be more gainful than previously found switching options
                            if gapBetweenWantedAndAvailableFlexDiff < gapBest and availableFlexDiff < gapInFlexBetweenBestAndWorstCl:
                                bw_best = bw
                                bb_best = bb
                                gapBest = gapBetweenWantedAndAvailableFlexDiff

                # also check if it is gainful to only move one BES from best cluster to worst cluster without replacing it by another BES

                availableFlexFromBestCluster = clusterListFlex[clIndexBest].listBesHP[bb].getFlexibility()

                # calculate new sums of power in clusters that would result from switching BESs
                nomPowerBesBestCl = abs(clusterListFlex[clIndexBest].listBesHP[bb].getNominalElectricalPower1())
                newPowerSumWorstCl = clusterPowerSumAbsHP[clIndexWorst] + nomPowerBesBestCl
                newPowerSumBestCl = clusterPowerSumAbsHP[clIndexBest] - nomPowerBesBestCl

                # check if switching these two BESs would cause one cluster to accumulate too much or too little nom. power
                if minClusterPowerSumAbsHP <= newPowerSumWorstCl <= maxClusterPowerSumAbsHP and minClusterPowerSumAbsHP <= newPowerSumBestCl <= maxClusterPowerSumAbsHP:

                    gapBetweenWantedAndAvailableFlexDiff = abs(wantedFlexDiff - availableFlexFromBestCluster)

                    # check if switching BESs would be more gainful than previously found switching options
                    if gapBetweenWantedAndAvailableFlexDiff < gapBest and availableFlexFromBestCluster < gapInFlexBetweenBestAndWorstCl:
                        bw_best = -1
                        bb_best = bb
                        gapBest = gapBetweenWantedAndAvailableFlexDiff


            # check if there are BESs that should be switched to distribute flexibility more equally
            if gapBest < float('inf'):
                # for debugging
                # if bw_best is not -1:
                    # print "Switch BES", bw_best+1, "(Cluster", clIndexWorst+1, ") and BES", bb_best+1, "(Cluster", clIndexBest+1, ")."
                # else:
                    # print "*** Move BES", bb_best+1, "(Cluster", clIndexBest+1, ") to Cluster", clIndexWorst+1, "***"

                # define BESs to be switched
                if bw_best is not -1:
                    besFromWorstCluster = clusterListFlex[clIndexWorst].listBesHP[bw_best]      # BES from worst cluster
                besFromBestCluster = clusterListFlex[clIndexBest].listBesHP[bb_best]            # BES from best cluster
                # switch chosen BESs
                if bw_best is not -1:
                    clusterListFlex[clIndexWorst].deleteMember(besFromWorstCluster)             # delete from worst cluster
                clusterListFlex[clIndexWorst].addMember(besFromBestCluster)                     # add to worst cluster
                clusterListFlex[clIndexBest].deleteMember(besFromBestCluster)                   # delete from worst cluster
                if bw_best is not -1:
                    clusterListFlex[clIndexBest].addMember(besFromWorstCluster)                 # add to worst cluster

                if bw_best is not -1:
                    # update sum of power for both clusters
                    clusterPowerSumAbsHP[clIndexWorst] = clusterPowerSumAbsHP[clIndexWorst] - abs(besFromWorstCluster.getNominalElectricalPower1()) + abs(besFromBestCluster.getNominalElectricalPower1())
                    clusterPowerSumAbsHP[clIndexBest] = clusterPowerSumAbsHP[clIndexBest] + abs(besFromWorstCluster.getNominalElectricalPower1()) - abs(besFromBestCluster.getNominalElectricalPower1())
                    # update sum of flexibility for both clusters
                    clusterFlexHP[clIndexWorst] = clusterFlexHP[clIndexWorst] - besFromWorstCluster.getFlexibility() + besFromBestCluster.getFlexibility()
                    clusterFlexHP[clIndexBest] = clusterFlexHP[clIndexBest] + besFromWorstCluster.getFlexibility() - besFromBestCluster.getFlexibility()
                else:
                    # update sum of power for both clusters
                    clusterPowerSumAbsHP[clIndexWorst] = clusterPowerSumAbsHP[clIndexWorst] + abs(besFromBestCluster.getNominalElectricalPower1())
                    clusterPowerSumAbsHP[clIndexBest] = clusterPowerSumAbsHP[clIndexBest] - abs(besFromBestCluster.getNominalElectricalPower1())
                    # update sum of flexibility for both clusters
                    clusterFlexHP[clIndexWorst] = clusterFlexHP[clIndexWorst] + besFromBestCluster.getFlexibility()
                    clusterFlexHP[clIndexBest] = clusterFlexHP[clIndexBest] - besFromBestCluster.getFlexibility()

            # break from switching loop, if there are no more HPs to be moved
            else:
                break

            loopGuard += 1
            if loopGuard > 500:
                print "loop guard breaks from while in HP switching."
                break


        # also make sure, that clusters have similar numbers of BESs
        numbersOfHPsInClusters = [clusterListFlex[c].getNumberOfPrimaryHeaters("HP") for c in range(n)]
        while float(max(numbersOfHPsInClusters) - min(numbersOfHPsInClusters)) / float(max(numbersOfHPsInClusters)) >= float(1)/float(3):

            if max(numbersOfHPsInClusters)-1 is min(numbersOfHPsInClusters):
                break

            minIndices = [c for c in range(len(numbersOfHPsInClusters)) if numbersOfHPsInClusters[c] is min(numbersOfHPsInClusters)]
            maxIndices = [c for c in range(len(numbersOfHPsInClusters)) if numbersOfHPsInClusters[c] is max(numbersOfHPsInClusters)]
            minFlexibilities = [clusterFlexHP[cb] for cb in minIndices]
            maxFlexibilities = [clusterFlexHP[cg] for cg in maxIndices]

            if len(minIndices) > len(maxIndices):
                for s in range(len(maxIndices)):
                    maxClusterHighestFlexIndex = maxIndices[np.argmax(maxFlexibilities)]
                    maxClusterFlex = max(maxFlexibilities)
                    minClusterLowestFlexIndex = minIndices[np.argmin(minFlexibilities)]
                    maxFlexibilities[np.argmax(maxFlexibilities)] = 0
                    minFlexibilities[np.argmin(minFlexibilities)] = float('inf')

                    besIndexFromGoodCluster = np.argmin([abs(maxClusterFlex - BES.getFlexibility() - avgFlexPerClusterHP) for BES in clusterListFlex[maxClusterHighestFlexIndex].listBesHP])
                    besFromGoodCluster = clusterListFlex[maxClusterHighestFlexIndex].listBesHP[besIndexFromGoodCluster]           # BES from best cluster

                    # print "+++ (HP) Move excess BES", besIndexFromGoodCluster+1, "(Cluster", maxClusterHighestFlexIndex+1, ") to poor little Cluster", minClusterLowestFlexIndex+1, "+++"
                    # switch chosen BESs
                    clusterListFlex[minClusterLowestFlexIndex].addMember(besFromGoodCluster)                     # add to worst cluster
                    clusterListFlex[maxClusterHighestFlexIndex].deleteMember(besFromGoodCluster)                   # delete from worst cluster
                    # update sum of power for both clusters
                    clusterPowerSumAbsHP[minClusterLowestFlexIndex] = clusterPowerSumAbsHP[minClusterLowestFlexIndex] + abs(besFromGoodCluster.getNominalElectricalPower1())
                    clusterPowerSumAbsHP[maxClusterHighestFlexIndex] = clusterPowerSumAbsHP[maxClusterHighestFlexIndex] - abs(besFromGoodCluster.getNominalElectricalPower1())
                    # update sum of flexibility for both clusters
                    clusterFlexHP[minClusterLowestFlexIndex] = clusterFlexHP[minClusterLowestFlexIndex] + besFromGoodCluster.getFlexibility()
                    clusterFlexHP[maxClusterHighestFlexIndex] = clusterFlexHP[maxClusterHighestFlexIndex] - besFromGoodCluster.getFlexibility()
            else:
                for s in range(len(minIndices)):
                    maxClusterHighestFlexIndex = maxIndices[np.argmax(maxFlexibilities)]
                    maxClusterFlex = max(maxFlexibilities)
                    maxFlexibilities[np.argmax(maxFlexibilities)] = 0
                    minFlexibilities[np.argmin(minFlexibilities)] = float('inf')

                    besIndexFromGoodCluster = np.argmin([abs(maxClusterFlex - BES.getFlexibility() - avgFlexPerClusterHP) for BES in clusterListFlex[maxClusterHighestFlexIndex].listBesHP])
                    besFromGoodCluster = clusterListFlex[maxClusterHighestFlexIndex].listBesHP[besIndexFromGoodCluster]           # BES from best cluster

                    # print "+++ (HP) Move excess BES", besIndexFromGoodCluster+1, "(Cluster", maxClusterHighestFlexIndex+1, ") to poor little Cluster", minIndices[s]+1, "+++"
                    # switch chosen BESs
                    clusterListFlex[minIndices[s]].addMember(besFromGoodCluster)                     # add to worst cluster
                    clusterListFlex[maxClusterHighestFlexIndex].deleteMember(besFromGoodCluster)                   # delete from worst cluster
                    # update sum of power for both clusters
                    clusterPowerSumAbsHP[minIndices[s]] = clusterPowerSumAbsHP[minIndices[s]] + abs(besFromGoodCluster.getNominalElectricalPower1())
                    clusterPowerSumAbsHP[maxClusterHighestFlexIndex] = clusterPowerSumAbsHP[maxClusterHighestFlexIndex] - abs(besFromGoodCluster.getNominalElectricalPower1())
                    # update sum of flexibility for both clusters
                    clusterFlexHP[minIndices[s]] = clusterFlexHP[minIndices[s]] + besFromGoodCluster.getFlexibility()
                    clusterFlexHP[maxClusterHighestFlexIndex] = clusterFlexHP[maxClusterHighestFlexIndex] - besFromGoodCluster.getFlexibility()

            numbersOfHPsInClusters = [clusterListFlex[c].getNumberOfPrimaryHeaters("HP") for c in range(n)]




########################################################################################################################
        # CHOOSE SCHEDULES (F)


        # have members of clusters choose their best schedules according to chosen criterion
        # loop through all created clusters


        if parallelizeLinux:
            if includeExecutionTimeLog:
                exec_time = 0
                startTimeCluster = time()
            chooseSchedulesProcs = []
            manager = mp.Manager()
            resultList = manager.list(range(n))
            for c in range(n):
                proc = mp.Process(target=chooseSchedulesHelper, args=(resultList, c, clusterListFlex[c], fromTime, criterion))
                proc.start()
                chooseSchedulesProcs.append(proc)
            for p in range(len(chooseSchedulesProcs)):
                chooseSchedulesProcs[p].join()
            for c in range(n):
                performances[1, h-startingHorizon, n_index, c] = resultList[c]
            if includeExecutionTimeLog:
                exec_time = time() - startTimeCluster
                logfile.write("\n\t\t\t--- time choosing schedules (PARALLEL flex. clustering): ({:.1f} members): {:.2f} s ---".format(float(noBes)/float(n), exec_time))
        else:
            exec_time = 0
            if includeExecutionTimeLog:
                startTimeCluster = time()
            for c in range(n):
                performances[1, h-startingHorizon, n_index, c] = clusterListFlex[c].chooseSchedules(fromTime=fromTime, criterion=criterion)
            if includeExecutionTimeLog:
                exec_time = time() - startTimeCluster
                logfile.write("\n\t\t\t--- time choosing schedules (SERIAL flex. clustering): ({:.1f} members): {:.2f} s ---".format(float(noBes)/float(n), exec_time))


        # evaluate quality of balanced clustering in terms of performance & similarity of performance
        medianPerformanceF = np.median(performances[1, h-startingHorizon, n_index, 0:n])    # find median of performances
        compactnessPerformanceF = np.sum([(medianPerformanceF - performances[1, h-startingHorizon, n_index, c]) ** 2 for c in range(n)]) / n    # calculate average square error per cluster
        greatestDiffOfTwoClustersF = max(performances[1, h-startingHorizon, n_index, 0:n]) - min(performances[1, h-startingHorizon, n_index, 0:n])



        ################################################################################################################
        # measure overall global performance (F)

        flucCurve = np.zeros(horizon/stepSize)
        remCurve = np.zeros(horizon/stepSize)
        for c in range(n):
            flucCurve += clusterListFlex[c].getFluctuationsCurve(fromTime, toTime)
            remCurve += clusterListFlex[c].getRemainder()
        overallPerformances[1, h-startingHorizon, n_index] = Cluster.calcPerformanceMeasure(remCurve, flucCurve, criterion)



########################################################################################################################
        # Provide logging


        if includeDebuggingInfo:
            logfile.write("\n\n\t\tPERFORMANCE OF BALANCING:")
            logfile.write("\n\t\tRandom:\t\tMed Perf: {:.3f}\t\t\tCompactness: {:.5f}\t Diff: {:.3f}".format(medianPerformanceR, compactnessPerformanceR, greatestDiffOfTwoClustersR))
            logfile.write("\n\t\tFlex.:\t\tMed Perf: {:.3f}\t\t\tCompactness: {:.5f}\t Diff: {:.3f}".format(medianPerformanceF, compactnessPerformanceF, greatestDiffOfTwoClustersF))

            logfile.write("\n\n\t\tInc (all):\tMed Perf: {:.2f} %\t\tCompactness: {:.2f} %\t Diff: {:.3f} %".format((medianPerformanceR - medianPerformanceF)/medianPerformanceR*100,
                                                                                                                    (compactnessPerformanceR - compactnessPerformanceF)/compactnessPerformanceR*100,
                                                                                                                    (greatestDiffOfTwoClustersR - greatestDiffOfTwoClustersF)/greatestDiffOfTwoClustersR*100))
        if includeExecutionTimeLog:
            logfile.write("\n\n\t\t\t--- Executing this cluster splitting: ({:.1f} members per cluster): {:.2f} s ---".format(float(noBes)/float(n), time() - startTimeClSplitting))

########################################################################################################################


    if includeExecutionTimeLog:
        logfile.write("\n\n\t\t--- Executing this day (day {}): {:.2f} s".format(h, time()-startTimeDay))
        logfile.close()

    # save arrays after each day as a backup
    np.save("{}/{}_h-{}.npy".format(dirResults, scenario_name, h), performances)
    np.save("{}/overall-{}_h-{}.npy".format(dirResults, scenario_name, h), overallPerformances)






            # print "\nClusters (CHP) (Day %i, %i clusters):" % (h, n)
        # for c in range(n):
        #     print "\t  ", c+1, "\t\t\t",
        # print ""
        # for b in range(max([len(clusterListFlex[c].listBesCHP) for c in range(n)])):
        #     for c in range(n):
        #         if b < clusterListFlex[c].getNumberOfPrimaryHeaters("CHP"):
        #             print "%06.0f - %06.1f\t | \t" % (abs(clusterListFlex[c].listBesCHP[b].getNominalElectricalPower1()), clusterListFlex[c].listBesCHP[b].getFlexibility()),
        #         else:
        #             print "\t\t\t\t | \t",
        #     print b+1
        # for c in range(n):
        #     print "---------------\t\t",
        # print ""
        # for c in range(n):
        #     print "%06.0f - %06.1f\t | \t" % (clusterPowerSumAbsCHP[c], clusterFlexCHP[c]),
        # print "%06.0f - %06.1f\n" % (avgPowerSumAbsPerClCHP, avgFlexPerClusterCHP),
