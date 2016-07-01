__author__ = 'Annika Wierichs'

from clustering.smartbes import SmartBes
from clustering.cluster import Cluster
from time import *
import os
import numpy as np
from building.environment import Environment
import matplotlib.pyplot as plt
import multiprocessing as mp
import itertools


noMem = 32  # number of members
noCl = 1    # number of clusters

# set values

stepSize = 3600
horizon = 86400*1
interval = 86400
fromTime = 86400*120
toTime = fromTime + horizon - stepSize
steps = horizon/stepSize


def ringSearchParMain(hPar, cl):
    # ring search: have buildings choose schedule that best flattens given fluctuations curve. update remainder accordingly. do this until all schedules are permanently set.




    schedulesChanged = np.ones(cl.getNumberOfMembers())   # has schedule of building h changed? -> 1
    h = hPar
    remainderTemp = cl.getFluctuationsCurve()
    while not np.all(schedulesChanged == 0):    # do ring search while not all schedules are permanently set
        print(h) # debugging
        (remainderTemp, schedulesChanged[h]) = cl.listBes[h].findBestSchedule(remainderTemp)
        if schedulesChanged[h] == -1:
            print "\nAt least one bes without any valid schedules. No results.\n"
            break
        if h < cl.getNumberOfMembers()-1:
            h += 1
        else:
            h = 0

    # calculate performance of chosen set of schedules
    avgRemainder = np.mean(remainderTemp)
    shiftedRemainder = [(remainderTemp[x]-avgRemainder) for x in range(0, len(remainderTemp))]
    cumsumShiftedRemainder = np.cumsum(shiftedRemainder)
    maxEnergyRemainder = max(abs(cumsumShiftedRemainder))
    deltaRemainder = np.max(remainderTemp) - np.min(remainderTemp)

    avgFluctuations = np.mean(cl.getFluctuationsCurve(fromTime, toTime))
    shiftedFluctuations = [(cl.getFluctuationsCurve(fromTime, toTime)[x]-avgFluctuations) for x in range(0, len(cl.getFluctuationsCurve(fromTime, toTime)))]
    cumsumFluctuations = np.cumsum(shiftedFluctuations)
    maxEnergyFluctuations = max(abs(cumsumFluctuations))
    deltaFluctuations = np.max(cl.getFluctuationsCurve(fromTime, toTime)) - np.min(cl.getFluctuationsCurve(fromTime, toTime))

    ratioMaxPower = deltaRemainder/deltaFluctuations

    print ratioMaxPower


def ringSearchParMainHelper(args):
    return ringSearchParMain(*args)


if __name__ == '__main__':

    # create folder for simulation results
    lt = localtime()
    dirResults = "_results_test_cluster/{}-{:02d}-{:02d}_{:02d}-{:02d}_MIP_clustersize".format(lt[0], lt[1], lt[2], lt[3], lt[4])
    if not os.path.exists(dirResults):
        os.makedirs(dirResults)
    dirScript = os.path.dirname(__file__)
    dirAbsResults = dirScript + "/" + dirResults

    environment1 = Environment(20, stepSize)

    # create smartbes objects
    clusterAllBes = Cluster(dirAbsResults, environment1, horizon, stepSize, interval)
    clusterAllBes.addRandomMembers(noMem)

    # calculate schedules and flexibility for each BES
    for b in range(clusterAllBes.getNumberOfMembers()):
        clusterAllBes.listBes[b].calcSchedulePool(fromTime=fromTime, toTimeH=toTime, absGap=2, solutionPoolIntensity=3)
        flex = clusterAllBes.listBes[b].calcFlexibility()

    besList = sorted(clusterAllBes.listBes, key = lambda smartbes: smartbes.getCurrentFlexibility())

    # for debugging
    print "\nFlex.\tNomPower\tFlex.*NomPower"
    for b in range(len(besList)):
        print '%.2f' % besList[b].flexibility,
        print "\t",
        print '%.0f' % besList[b].getNominalElectricalPower1(),
        print "\t\t",
        print '%.2f' % besList[b].flexibilityInclNomPower

    # split into equally flexible clusters
    clusterList = list()
    ratioMaxEnergy = list()
    ratioMaxPower = list()
    for i in range(noCl):
        clusterList.append(Cluster(dirAbsResults, environment1, horizon, stepSize, interval))
    for c in range(noCl):
        for i in range(len(besList)/noCl):
            clusterList[c].addMember(besList[i*noCl+c])
        # choose schedules for BES's in each cluster and measure performance
        clusterList[c].sortMembers(11)

        toTime = fromTime + (steps - 1) * stepSize
        remainderTemp = clusterList[c].getFluctuationsCurve(fromTime, toTime)     # current remainder (changes with each iteration)

        # have buildings calculate possible optimal schedules and reset data for ring search
        for h in range(clusterList[c].getNumberOfMembers()):
            # if not self.listBes[h].schedules:   # todo: macht sinn? ne.
            #     self.listBes[h].calcSchedulePool(fromTime, toTime, solutionPoolIntensity=3)
            clusterList[c].listBes[h].resetForDesync(steps)

        hPar = range(clusterList[c].getNumberOfMembers())
        paraCl = clusterList[c]
        pool = mp.Pool()
        pool.map_async(ringSearchParMainHelper, itertools.izip(hPar, itertools.repeat(paraCl)))
        pool.close()
        pool.join()
        # resPwr = resTemp.get()
        # print resPwr


# plot results for debugging
# N = len(ratioMaxEnergy)
# ind = np.arange(N)  # the x locations for the groups
# width = 0.35       # the width of the bars
# fig, ax = plt.subplots()
# rects1 = ax.bar(ind, ratioMaxEnergy, width, color='r')
# rects2 = ax.bar(ind+width, ratioMaxPower, width, color='y')
# ax.legend( (rects1[0], rects2[0]), ('Energy', 'Power') )
# plt.show()