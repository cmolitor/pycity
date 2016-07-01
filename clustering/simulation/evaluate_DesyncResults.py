__author__ = 'Annika Wierichs'

import numpy as np#
import os

# !!! insert correct file name here !!!
dirScript = os.path.dirname(__file__)
pathMulti = dirScript + '/_results_clustering_multiDSync/multiDSync_days-365_RES-020/performances_8ClS_365Days_Start0-_h-362.npy'
pathSorted = dirScript + '/_results_clustering_sortedDSync/sortedDSync_days-365_RES-020/performances_8ClS_365Days_Start0-_h-362.npy'

# load results
multiDesync = np.load(pathMulti)
sortedDesync = np.load(pathSorted)

noDays = multiDesync.shape[0]
noClusterSplitting = multiDesync.shape[1]   # number of different cluster splittings

# create array that holds the number of members per cluster for each cluster splitting
noOfMembersInCluster = np.zeros(noClusterSplitting)
for s in range(noClusterSplitting):
    noOfMembersInCluster[s] = np.count_nonzero(multiDesync[0,s])

bestMulti = np.array([ [ min(multiDesync[h, s, 0:noOfMembersInCluster[s]]) for s in range(noClusterSplitting) ] for h in range(noDays) ])
multiBestAvg = [ np.mean(bestMulti[:, s]) for s in range(noClusterSplitting)]
sortedAvg = [ np.mean(sortedDesync[:, s]) for s in range(noClusterSplitting)]

improvementPerSpl = [(multiBestAvg[s]-sortedAvg[s])/multiBestAvg[s] for s in range(noClusterSplitting) ]

print "multi best avg per splitting:\t", multiBestAvg
print "sorted avg per splitting:\t\t", sortedAvg
print "improvement:\t\t\t\t\t", improvementPerSpl