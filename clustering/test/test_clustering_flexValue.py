__author__ = 'Annika Wierichs'

from clustering.cluster import Cluster
from building.environment import Environment
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

# create environment & cluster that generates and holds all SmartBES objects
env = Environment(20, stepSize)
clusterAllBes = Cluster(dirAbsResults, env, horizon, stepSize, interval)
clusterAllBes.addRandomMembers(noMem, pseudorandom=True)
noMemPH = clusterAllBes.getNumberOfPrimaryHeaters("all")

# calculate schedules and flexibility for each BES
for b in range(clusterAllBes.getNumberOfMembers()):
    clusterAllBes.listBes[b].calcSchedulePool(fromTime=fromTime, toTimeH=toTime, absGap=2, solutionPoolIntensity=4)
    flex = clusterAllBes.listBes[b].calcFlexibility()

# create lists of CHP-BES and HP-BES. sort by Flex*NomPower for proper assignment to clusters later.
besListCHP = [b for b in clusterAllBes.listBes if b.getNominalElectricalPower1() < 0]       # CHP
besListHP = [b for b in clusterAllBes.listBes if b.getNominalElectricalPower1() > 0]        # HP
besListNoFlex = [b for b in clusterAllBes.listBes if b.getNominalElectricalPower1() == 0]   # no thermal storage

besListCHP = sorted(besListCHP, key = lambda smartbes: smartbes.getCurrentFlexibilityInclNomPower())
besListHP = sorted(besListHP, key = lambda smartbes: smartbes.getCurrentFlexibilityInclNomPower(), reverse=True)    # reverse for descending order

# create specified number of clusters and save in clusterList
clusterList = list()
for i in range(noCl):
    clusterList.append(Cluster(dirAbsResults, env, horizon, stepSize, interval))

# assign BES's to clusters, so that Flex*NomPower value will be similar for all clusters.
# add BES in order of sorted list (starting with highest Flex*NomPower value), always adding BES to cluster with lowest accumulated Flex*NomPower value. This works quite well.
clusterFlexPowSumCHP = [0 for i in range(noCl)]
for b in range(len(besListCHP)):
    clIndex = np.argmax(clusterFlexPowSumCHP)  # add to the cluster currently accumulating lowest Flex*NomPower value (max since values are negative for CHPs)
    clusterList[clIndex].addMember(besListCHP[b])
    clusterFlexPowSumCHP[clIndex] += besListCHP[b].getCurrentFlexibilityInclNomPower()
# assign HP-BES to cluster
clusterFlexPowSumHP = [0 for i in range(noCl)]
for b in range(len(besListHP)):
    clIndex = np.argmin(clusterFlexPowSumHP)    # add to the cluster currently accumulating lowest Flex*NomPower value
    clusterList[clIndex].addMember(besListHP[b])
    clusterFlexPowSumHP[clIndex] += besListHP[b].getCurrentFlexibilityInclNomPower()
# equally assign BES that only add load to clusters
for b in range(len(besListNoFlex)):
    clusterList[b%noCl].addMember(besListNoFlex[b])

# for debugging: print clusters
# print "\nFlex.\tNomPower\tFlex.*NomPower"
# for c in range(noCl):
#     print "Cluster ", c+1, "- CHP-Sum:", clusterFlexPowSumCHP[c], " /  HP-Sum:", clusterFlexPowSumHP[c]
#     for b in range(len(clusterList[c].listBes)):
#         print '%.2f' % clusterList[c].listBes[b].flexibility,
#         print "\t",
#         print '%.0f' % clusterList[c].listBes[b].getNominalElectricalPower1(),
#         print "\t\t",
#         print '%.2f' % clusterList[c].listBes[b].getCurrentFlexibilityInclNomPower()

# sort members of clusters & have them choose their best schedules according to either power or energy criterion
ratioMaxEnergy = list()
ratioMaxPower = list()
for c in range(noCl):
    clusterList[c].sortMembers(11)
    (rme, rmp) = clusterList[c].chooseSchedules(fromTime=fromTime, criterion=crit)   # choose 'power' or 'energy'
    ratioMaxEnergy.append(rme)
    ratioMaxPower.append(rmp)
    print "\nCluster No. ", c+1, ":"
    print "Sum of nom. power:\nPrim. H.:", clusterList[c].getSumOfNomElecPower("all"), "\t\tCHPs:", clusterList[c].getSumOfNomElecPower("CHP"), "\t\tHPs:", clusterList[c].getSumOfNomElecPower("HP")
    print "Prim. H.:", clusterList[c].getNumberOfPrimaryHeaters("all"), "\t\tCHPs:", clusterList[c].getNumberOfPrimaryHeaters("CHP"), "\t\tHPs:", clusterList[c].getNumberOfPrimaryHeaters("HP")
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