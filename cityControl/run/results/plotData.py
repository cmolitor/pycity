import numpy as np 
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import fnmatch

listSim = list()

dirResults = "/Users/christoph/Documents/PythonProjects/cm116988_clustersizeanalysis/cityControl/run/results/"

for root, dirs, files in os.walk(dirResults):
	#print(dirs)
	# 2015-03-11_12-19_startH-0_stepSize-900_shareRES-20_clusterSize-60_RSC-3_L_FINAL
	listSim += fnmatch.filter(dirs, '*_start*-0_*stepSize-900_shareRES-20_clusterSize-*_FINAL')

#_newData = np.load("/Users/christoph/Documents/PythonProjects/cm116988_clustersizeanalysis/cityControl/run/results/2015-03-08_10-52_startH-0_stepSize-900_shareRES-20_clusterSize-60_RSC-3_GL/remainders.npy")
#_newData = np.load("/Users/christoph/Documents/PythonProjects/cm116988_clustersizeanalysis/cityControl/run/results/2015-03-08_10-52_startH-0_stepSize-900_shareRES-20_clusterSize-60_RSC-3_GL/fluctuations.npy")
#print(_newData.shape)

# for r in range(0, len(listSim)):
# 	fpath = dirResults + listSim[r] + "/"

# 	if os.path.exists(fpath): 
# 		print(listSim[r])
# 		fluctuations = np.load(fpath + "fluctuations.npy")
# 		remainders = np.load(fpath + "remainders.npy")
# 		print fluctuations.shape
# 		print remainders.shape
# 		#_newData[1,:] = fluctuations.T
# 		#print fluctuations.shape
# 		#print _newData.shape
# 		#np.save(dirResults + listSim[r] + "/fluctuations.npy", _newData)
# 		#np.savetxt(dirResults + listSim[r] + "/fluctuations.txt", _newData)
# exit()

fromTime = 86400 * (31+28+31+30+31+30) # 0 # (31+28+31)  # (31+28+31+30+31+30)
toTime = 86400 * (31+28+31+30+31+30+31) # 31 # (31+28+31+30)  # (31+28+31+30+31+30+31)

for r in range(0, len(listSim)):
	fig = plt.figure(figsize=(4, 2.5), dpi=500)
	gs = mpl.gridspec.GridSpec(1, 1) # , height_ratios=[1, 1]

	ax1 = plt.subplot(gs[0])
	listPlots = list()
	listPlotLegends = list()

	fpath = dirResults + listSim[r] + "/"
	print(listSim[r])
	fluctuations = np.load(fpath + "fluctuations.npy")
	fluctuations = fluctuations.T

	remainders = np.load(fpath + "remainders.npy")
	remainders = remainders.T

	performances = np.load(fpath + "performances.npy")
	annualRPV = np.sum(performances)
	print(annualRPV)

	ax1.plot(fluctuations[(fromTime < fluctuations[:,0])*(fluctuations[:,0]<toTime),1])
	ax1.plot(remainders[(fromTime < remainders[:,0])*(remainders[:,0]<toTime),1])

	fig.savefig(fpath + "results.pdf")

	#fluctuations2 = np.reshape(fluctuations, (fluctuations.shape[0]*fluctuations.shape[1],-1), order="F")

#remainder = np.load(dirResults + "remainders.npy")
#remainder = remainder.T
#remainder2 = np.reshape(remainder, (remainder.shape[0]*remainder.shape[1],-1), order="F")

#plt.plot(fluctuations2)
#plt.plot(remainder2)
#plt.plot(fluctuations2[0:96])

#plt.show()