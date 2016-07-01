import numpy as np
import os
import fnmatch
import re

dirResults = "/Users/christoph/Documents/PythonProjects/cm116988_clustersizeanalysis/cityControl/run/results/"
dirResults = "/Users/christoph/Documents/Dissertation/03_SimulationResults/Ch_CoordConcept/Diverse_scenarios/"
dirResults = "/Users/christoph/Documents/PythonProjects/cm116988_clustersizeanalysis/cityControl/run/results/"

folderScenario = list()

for root, dirs, files in os.walk(dirResults):
	# print(dirs)
	# 2015-03-17_11-24_startI-0_stopI-365_stepSize-900_shareRES-50_clusterSize-50_RSC-3_L_FINAL
	folderScenario += fnmatch.filter(dirs, '*_startI*stepSize-900_shareRES-50_clusterSize-*_RSC-3_*')
	#2015-03-22_11-19_startI-0_stopI-365_stepSize-900_shareRES-50_clusterSize-100_RSC-3_PIDA_Seed-1_FINAL_x2

for x in range(0, len(folderScenario)):
	#print folderScenario[x]
	data = np.load(dirResults + folderScenario[x] + "/performances.npy")
	#print data.shape, len(data.shape)

	if len(data.shape) == 1:
		print "here: ", folderScenario[x]
		startI = int(re.findall(r'\d+', folderScenario[x])[5])
		stopI = int(re.findall(r'\d+', folderScenario[x])[6])
		_range = np.arange(startI, stopI)
		dataNew = np.zeros((len(_range), 2))
		dataNew[:,0] = _range
		dataNew[:,1] = data

		os.rename(dirResults + folderScenario[x] + "/performances.npy", dirResults + folderScenario[x] + "/performances_org.npy")
		os.rename(dirResults + folderScenario[x] + "/performances.txt", dirResults + folderScenario[x] + "/performances_org.txt")
		np.save(dirResults + folderScenario[x] + "/performances.npy", dataNew)
		np.savetxt(dirResults + folderScenario[x] + "/performances.txt", dataNew)


		#print dataNew

