__author__ = 'Annika Wierichs'

# random assignment of BES to clusters for comparison

from clustering.cluster import Cluster
from building.environment import Environment
from time import *

import os
import numpy as np
import matplotlib.pyplot as plt
import random

noMem = 40     # number of members
noCl = 4        # number of clusters
crit = 'energy'  # criterion will be applied to find best schedule in BES and best ring search iteration in cluster

# set values
stepSize = 3600
horizon = 86400
interval = 86400
fromTime = 86400*250
toTime = fromTime + horizon - stepSize

# create folder for simulation results
lt = localtime()
dirResults = "_results_test_cluster/{}-{:02d}-{:02d}_{:02d}-{:02d}_MIP_clustersize".format(lt[0], lt[1], lt[2], lt[3], lt[4])
if not os.path.exists(dirResults):
    os.makedirs(dirResults)
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

# create environment & cluster that generates and holds all SmartBES objects
env = Environment(20, stepSize)
clusterAllBes = Cluster(dirAbsResults, env, horizon, stepSize, interval)
clusterAllBes.addRandomMembers(noMem, pseudorandom=True)
noMemPH = clusterAllBes.getNumberOfPrimaryHeaters("all")

# calculate schedules for each BES
for b in range(clusterAllBes.getNumberOfMembers()):
    clusterAllBes.listBes[b].calcSchedulePool(fromTime=fromTime, toTimeH=toTime, absGap=2, solutionPoolIntensity=4)

# create specified number of clusters and save randomly in clusterList
random.seed(6)  # for reproducibility
randomIndexes = random.sample(range(noMem), noMem)
clusterList = list()
for c in range(noCl):
    clusterList.append(Cluster(dirAbsResults, env, horizon, stepSize, interval))
    for b in range(noMem/noCl):
        clusterList[c].addMember(clusterAllBes.listBes[randomIndexes[c*noCl+b]])

# # for debugging: print clusters
# print "\nFlex.\tNomPower\tFlex.*NomPower"
# for c in range(noCl):
#     print "Cluster ", c+1, "- CHP-Sum:", clusterFlexPowSumCHP[c], " /  HP-Sum:", clusterFlexPowSumHP[c]
#     for b in range(len(clusterList[c].listBes)):
#         print '%.2f' % clusterList[c].listBes[b].flexibility,
#         print "\t",
#         print '%.0f' % clusterList[c].listBes[b].getNominalElectricalPower1(),
#         print "\t\t",
#         print '%.2f' % clusterList[c].listBes[b].getCurrentFlexibilityInclNomPower()

# for debugging:
print "\nNo. of available Prim. H.: "
print "All: ", noMemPH, "\t\tCHP: ", clusterAllBes.getNumberOfPrimaryHeaters("CHP"), "\t\tHP: ", clusterAllBes.getNumberOfPrimaryHeaters("HP"), "\n"

# have clusters choose their best schedules according to either power or energy criterion
ratioMaxEnergy = list()
ratioMaxPower = list()
for c in range(noCl):
    # clusterList[c].sortMembers(11)
    (rme, rmp) = clusterList[c].chooseSchedules(fromTime=fromTime, criterion=crit)
    ratioMaxEnergy.append(rme)
    ratioMaxPower.append(rmp)
    print "\nCluster No. ", c+1, ":"
    print "Sum of nom. power:\nPrim. H.:", clusterList[c].getSumOfNomElecPower("all"), "\t\tCHPs:", clusterList[c].getSumOfNomElecPower("CHP"), "\t\tHPs:", clusterList[c].getSumOfNomElecPower("HP")
    print "Prim. H.: ", clusterList[c].getNumberOfPrimaryHeaters("all"), "\t\tCHPs: ", clusterList[c].getNumberOfPrimaryHeaters("CHP"), "\t\tHPs: ", clusterList[c].getNumberOfPrimaryHeaters("HP")
    print "Ratio Max Energy: ", ratioMaxEnergy[c],
    print "\tRatio Max Power: ", ratioMaxPower[c]

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

# plot results for debugging: check if cluster-results are similar
N = len(ratioMaxEnergy)
ind = np.arange(N)  # the x locations for the groups
width = 0.35       # the width of the bars
fig, ax = plt.subplots()
rects1 = ax.bar(ind, ratioMaxEnergy, width, color='r')
rects2 = ax.bar(ind+width, ratioMaxPower, width, color='y')
ax.legend( (rects1[0], rects2[0]), ('Energy', 'Power') )
plt.show()