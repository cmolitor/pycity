__author__ = 'Annika'

from clustering.cluster import Cluster
from building.environment import Environment
from city.database import DataBase
from time import *

import os
import numpy as np
import matplotlib.pyplot as plt

noMem = 60      # number of members
noCl = 4        # number of clusters
crit = 'power'  # criterion will be applied to find best schedule in BES and best ring search iteration in cluster

# set values
stepSize = 3600
horizon = 86400
interval = 86400
fromTime = 86400*250
toTime = fromTime + horizon - stepSize
steps = horizon/stepSize

# create folder for simulation results
lt = localtime()
dirResults = "_results_test_cluster/{}-{:02d}-{:02d}_{:02d}-{:02d}_MIP_clustersize".format(lt[0], lt[1], lt[2], lt[3], lt[4])
if not os.path.exists(dirResults):
    os.makedirs(dirResults)
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

# create environment & random buildings
env = Environment(20, stepSize)
allBesList = DataBase.createRandomBuildings(noMem, stepSize, pseudorandom=True, randomSeed=1)

# calculate schedules and impact-array for each BES
for b in range(noMem):
    allBesList[b].calcSchedulePool(fromTime=fromTime, toTimeH=toTime, absGap=2, solutionPoolIntensity=4)
    allBesList[b].calcImpactArrayAbs()

# create lists of CHP-BES and HP-BES.
besListCHP = [b for b in allBesList if b.getNominalElectricalPower1() < 0]       # CHP
besListHP = [b for b in allBesList if b.getNominalElectricalPower1() > 0]        # HP
besListNoFlex = [b for b in allBesList if b.getNominalElectricalPower1() == 0]   # no thermal storage
noPH = len(besListCHP) + len(besListHP)
# sort lists by sum of impact-probabilities, descending
besListCHP = sorted(besListCHP, key = lambda smartbes: sum(smartbes.impactArray), reverse=True)
besListHP = sorted(besListHP, key = lambda smartbes: sum(smartbes.impactArray), reverse=True)

# calculate avg impact values PER BES for each time step for CHPs and HPs
impactsCHP = np.array([besListCHP[x].impactArray for x in range(len(besListCHP))])
impactsHP = np.array([besListHP[x].impactArray for x in range(len(besListHP))])
avgImpactsCHP = np.array(impactsCHP.sum(axis=0)) / len(besListCHP)
avgImpactsHP = np.array(impactsHP.sum(axis=0)) / len(besListHP)
# calculate average impact values PER CLUSTER for each time step
avgAccImpactPerClusterCHP =  sum(avgImpactsCHP) * len(besListCHP) / noCl
avgAccImpactPerClusterHP = sum(avgImpactsHP) * len(besListHP) / noCl

# create specified number of clusters and save in clusterList
clusterList = list()
for i in range(noCl):
    clusterList.append(Cluster(dirAbsResults, env, horizon, stepSize, interval))

# assignment of BES to clusters (CHPs and HPs seperately)
# -------------------------------------------------------

# CHPs
# ---
# setup some loop-variables
impactAccumulatedInCls = np.zeros([noCl, steps])    # holds accumulated impact per time step for each cluster
absBenefit = np.zeros(steps)                        # benefit for each time step that the adding of a given BES to a given cluster would have. temporary variable inside loops.
avgBenefit = np.zeros(noCl)                         # average benefit per time step that the adding of a given BES to a given cluster would have

# add one BES to each cluster to begin with. these are the BES's with great impact values since list has been sorted.
for c in range(noCl):
    clusterList[c].addMember(besListCHP[c])
    impactAccumulatedInCls[c] = np.array(besListCHP[c].impactArray)

# now add remaining BES to clusters
for b in range(noCl, len(besListCHP)):  # loop through all remaining BES
    impArrayTemp = np.array(besListCHP[b].impactArray)

    # check the impact of current BES on each existing cluster to evaluate which cluster benefits most from this BES
    for c in range(noCl):
        # save current average-array and the average array that would result from adding current BES to this cluster
        avgArrayOld = np.array(impactAccumulatedInCls[c]) / clusterList[c].getNumberOfPrimaryHeaters("CHP")
        avgArrayNew = np.array((impactAccumulatedInCls[c] + impArrayTemp)) / (clusterList[c].getNumberOfPrimaryHeaters("CHP") + 1) # +1 for correct avg since BES hasn't actually been added to cluster yet.

        # calculate the benefit that this cluster would draw from having current BES added to it, except it already has enough members to score above average-impact-sum
        # if sum(impactAccumulatedInCls[c]) > avgAccImpactPerClusterCHP * 1.1:
        if clusterList[c].getNumberOfPrimaryHeaters("CHP") > len(besListCHP)/noCl:
            avgBenefit[c] = -float("inf")   # make sure this cluster won't be chosen by algorithm
        else:
            # evaluate each time step seperately. if branching is necessary to cover all possible cases of the new BES influencing the avg impacts of this cluster.
            for t in range(len(avgImpactsCHP)):
                if avgArrayOld[t] < avgImpactsCHP[t]:
                    if avgArrayNew[t] > avgImpactsCHP[t]:
                        absBenefit[t] = 2*avgImpactsCHP[t] - avgArrayNew[t] - avgArrayOld[t]
                    else:
                        absBenefit[t] = avgArrayNew[t] - avgArrayOld[t]
                else:
                    if avgArrayNew[t] < avgImpactsCHP[t]:
                        absBenefit[t] = -2*avgImpactsCHP[t] + avgArrayNew[t] + avgArrayOld[t]
                    else:
                        absBenefit[t] = avgArrayOld[t] - avgArrayNew[t]
            # calculate average benefit of all time steps
            avgBenefit[c] = absBenefit.sum() / len(absBenefit)

    # choose cluster for which this BES is most beneficial in terms of bringing avg impacts of BES's of this cluster closer to the avg impact of all BES
    clIndex = np.argmax(avgBenefit)
    #print clIndex,  # for debugging
    pltImpactAvgOld = np.array(impactAccumulatedInCls[clIndex]) / clusterList[clIndex].getNumberOfPrimaryHeaters("CHP")     # for debugging
    clusterList[clIndex].addMember(besListCHP[b])                                                                           # add to chosen cluster
    impactAccumulatedInCls[clIndex] = impactAccumulatedInCls[clIndex] + np.array(besListCHP[b].impactArray)                 # update the accumulated impact array of this cluster
    pltImpactAvgNew = np.array(impactAccumulatedInCls[clIndex]) / clusterList[clIndex].getNumberOfPrimaryHeaters("CHP")     # for debugging
    # plot for debugging
    xAxis = [x for x in range(1, steps+1)]
    plt.plot(xAxis, avgImpactsCHP, 'r-', xAxis, pltImpactAvgOld, 'b-', xAxis, pltImpactAvgNew, 'g-')
    plt.show()


# HPs
# ---
# setup some loop-variables
impactAccumulatedInCls = np.zeros([noCl, steps])    # holds accumulated impact per time step for each cluster
absBenefit = np.zeros(steps)                        # benefit for each time step that the adding of a given BES to a given cluster would have. temporary variable inside loops.
avgBenefit = np.zeros(noCl)                         # average benefit per time step that the adding of a given BES to a given cluster would have

# add one BES to each cluster to begin with. these are the BES's with great impact values since list has been sorted.
for c in range(noCl):
    clusterList[c].addMember(besListHP[c])
    impactAccumulatedInCls[c] = np.array(besListHP[c].impactArray)

# now add remaining BES to clusters
for b in range(noCl, len(besListHP)):  # loop through all remaining BES
    impArrayTemp = np.array(besListHP[b].impactArray)

    # check the impact of current BES on each existing cluster to evaluate which cluster benefits most from this BES
    for c in range(noCl):
        # save current average-array and the average array that would result from adding current BES to this cluster
        avgArrayOld = np.array(impactAccumulatedInCls[c]) / clusterList[c].getNumberOfPrimaryHeaters("HP")
        avgArrayNew = np.array((impactAccumulatedInCls[c] + impArrayTemp)) / (clusterList[c].getNumberOfPrimaryHeaters("HP") + 1) # +1 for correct avg since BES hasn't actually been added to cluster yet.

        # calculate the benefit that this cluster would draw from having current BES added to it, except it already has enough members to score above average-impact-sum
        #if sum(impactAccumulatedInCls[c]) > avgAccImpactPerClusterHP * 1.1:
        if clusterList[c].getNumberOfPrimaryHeaters("all") > noPH/noCl:
            avgBenefit[c] = -float("inf")   # make sure this cluster won't be chosen by algorithm
        else:
            # evaluate each time step seperately. if branching is necessary to cover all possible cases of the new BES influencing the avg impacts of this cluster.
            for t in range(len(avgImpactsHP)):
                if avgArrayOld[t] < avgImpactsHP[t]:
                    if avgArrayNew[t] > avgImpactsHP[t]:
                        absBenefit[t] = 2*avgImpactsHP[t] - avgArrayNew[t] - avgArrayOld[t]
                    else:
                        absBenefit[t] = avgArrayNew[t] - avgArrayOld[t]
                else:
                    if avgArrayNew[t] < avgImpactsHP[t]:
                        absBenefit[t] = -2*avgImpactsHP[t] + avgArrayNew[t] + avgArrayOld[t]
                    else:
                        absBenefit[t] = avgArrayOld[t] - avgArrayNew[t]
            # calculate average benefit of all time steps
            avgBenefit[c] = absBenefit.sum() / len(absBenefit)

    # choose cluster for which this BES is most beneficial in terms of bringing avg impacts of BES's of this cluster closer to the avg impact of all BES
    clIndex = np.argmax(avgBenefit)
    # print clIndex,  # for debugging
    pltImpactAvgOld = np.array(impactAccumulatedInCls[clIndex]) / clusterList[clIndex].getNumberOfPrimaryHeaters("HP")     # for debugging
    clusterList[clIndex].addMember(besListHP[b])                                                                           # add to chosen cluster
    impactAccumulatedInCls[clIndex] = impactAccumulatedInCls[clIndex] + np.array(besListHP[b].impactArray)                 # update the accumulated impact array of this cluster
    pltImpactAvgNew = np.array(impactAccumulatedInCls[clIndex]) / clusterList[clIndex].getNumberOfPrimaryHeaters("HP")     # for debugging
    # plot for debugging
    xAxis = [x for x in range(1, steps+1)]
    plt.plot(xAxis, avgImpactsHP, 'r-', xAxis, pltImpactAvgOld, 'b-', xAxis, pltImpactAvgNew, 'g-')
    plt.show()


# gas boiler BES's
# ----------------
# equally assign BES that only add load to clusters
for b in range(len(besListNoFlex)):
    clusterList[b%noCl].addMember(besListNoFlex[b])

# for debugging:
print "\nNo. of available Prim. H.: "
print "All: ", noPH, "\t\tCHP: ", len(besListCHP), "\t\tHP: ", len(besListHP), "\n"

# have members of clusters choose their best schedules according to chosen criterion
ratioMaxEnergy = list()
ratioMaxPower = list()
for c in range(noCl):
    clusterList[c].sortMembers(21)
    (rme, rmp) = clusterList[c].chooseSchedules(fromTime=fromTime, criterion=crit)
    ratioMaxEnergy.append(rme)
    ratioMaxPower.append(rmp)
    print "\nCluster No. ", c+1, ":"
    print "Sum of nom. power:\nPrim. H.:", clusterList[c].getSumOfNomElecPower("all"), "\t\tCHPs:", clusterList[c].getSumOfNomElecPower("CHP"), "\t\tHPs:", clusterList[c].getSumOfNomElecPower("HP")
    print "Prim. H.:", clusterList[c].getNumberOfPrimaryHeaters("all"), "\t\tCHPs:", clusterList[c].getNumberOfPrimaryHeaters("CHP"), "\t\tHPs:", clusterList[c].getNumberOfPrimaryHeaters("HP")
    print "Ratio Max Energy: ", ratioMaxEnergy[c],    # for debugging
    print "\tRatio Max Power: ", ratioMaxPower[c]     # for debugging

# quantify similarity of performance of clusters depending on criterion used
if crit == 'power':
    avgPowerRatio = sum(ratioMaxPower) / noCl
    perctgDeviationFromAvg = ( sum([abs(ratioMaxPower[c]-avgPowerRatio) for c in range(noCl)]) / noCl ) / avgPowerRatio
    perctgGreatestDiffOfTwoClusters = (max(ratioMaxPower) - min(ratioMaxPower)) / ((max(ratioMaxPower) + min(ratioMaxPower)) / 2)
    print "\n\nSimilarity of clusters:"
    print "Average deviation of power ratio from average (percentage):", perctgDeviationFromAvg
    print "Greatest difference of power ratios of two clusters (percentage):", perctgGreatestDiffOfTwoClusters
elif crit == 'energy':
    avgEnergyRatio = sum(ratioMaxEnergy) / noCl
    perctgDeviationFromAvg = ( sum([abs(ratioMaxEnergy[c]-avgEnergyRatio) for c in range(noCl)]) / noCl ) / avgEnergyRatio
    perctgGreatestDiffOfTwoClusters = (max(ratioMaxEnergy) - min(ratioMaxEnergy)) / ((max(ratioMaxEnergy) + min(ratioMaxEnergy)) / 2)
    print "\n\nSimilarity of clusters:"
    print "Average deviation of energy ratio from average (percentage):", perctgDeviationFromAvg
    print "Greatest difference of energy ratios of two clusters (percentage):", perctgGreatestDiffOfTwoClusters

# plot for debugging: check if cluster-results are similar
N = len(ratioMaxEnergy)
ind = np.arange(N)  # the x locations for the groups
width = 0.35       # the width of the bars
fig, ax = plt.subplots()
rects1 = ax.bar(ind, ratioMaxEnergy, width, color='r')
rects2 = ax.bar(ind+width, ratioMaxPower, width, color='y')
ax.legend( (rects1[0], rects2[0]), ('Energy', 'Power') )
plt.show()