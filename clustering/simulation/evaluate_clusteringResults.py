__author__ = 'Annika Wierichs'

import numpy as np
import os

dirScript = os.path.dirname(__file__)
path = dirScript + '/_results_clustering_flexValue/FullYear_SortedDesync_new/performances.npy'

# load results
results = np.load(path)

# read some data for evaluation
noDays = results.shape[1]
noOfClSplittings = results.shape[2]
noOfClustersRange = np.zeros(noOfClSplittings)
for n_index in range(noOfClSplittings):
    noOfClustersRange[n_index] = np.count_nonzero(results[0, 0, n_index])


res = np.zeros([2,365,4,30])
res[:, :, 0, 0:05] = results[:, :, 1, 0:05]
res[:, :, 1, 0:10] = results[:, :, 1, 0:10]
res[:, :, 2, 0:20] = results[:, :, 1, 0:20]
res[:, :, 3, 0:30] = results[:, :, 1, 0:30]

# evaluate data
compactnessAll = np.zeros([2, noDays, 4])
meanAll = np.zeros([2, noDays, 4])
for a in range(2):
    for d in range(noDays):
        for n in range(4):
            performancesArrayTemp = [ res[a, d, n, c] for c in range(np.count_nonzero(res[0,0,n])) ]
            meanAll[a, d, n] = np.mean(performancesArrayTemp)
            compactnessAll[a, d, n] = np.sum( [ (meanAll[a, d, n] - performancesArrayTemp[c]) ** 2 for c in range(np.count_nonzero(res[0,0,n])) ] ) / np.count_nonzero(res[0,0,n])

compactnessRanAvgPerS = [ np.mean(compactnessAll[0, :, n]) for n in range(4) ]
compactnessManAvgPerS = [ np.mean(compactnessAll[1, :, n]) for n in range(4) ]

for n in range(4):
    print "compactness R:\t",  compactnessRanAvgPerS[n],
    print "\t\tM:", compactnessManAvgPerS[n]