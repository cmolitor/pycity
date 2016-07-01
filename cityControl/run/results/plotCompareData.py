import numpy as np 
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import fnmatch

pgf_with_custom_preamble = {
    # "pgf.texsystem" : "pdflatex",
    "font.family": "serif", # use serif/main font for text elements
    "font.size": 7,
    "axes.labelsize": 7,
    "text.fontsize": 7,
    "legend.fontsize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "lines.linewidth": 0.5,
    "axes.linewidth": 0.5,
    # "text.usetex": True,    # use inline math for ticks
    "pgf.rcfonts": False,   # don't setup fonts from rc parameters
    "pgf.preamble": [
         r"\usepackage{units}",         # load additional packages
         r"\usepackage{metalogo}",
         r"\usepackage{unicode-math}",  # unicode math setup
         r"\setmathfont{xits-math.otf}",
         r"\setmainfont{ae}", # serif font via preamble
        ]
}
mpl.rcParams.update(pgf_with_custom_preamble)

#==========================================
# Color definitions
#==========================================

# some colors: http://help.dottoro.com/lanifqvh.php
colors = list()
colors.append("#332288")
colors.append("#88CCEE")
colors.append("#44AA99")
colors.append("#117733")
colors.append("#999933")
colors.append("#DDCC77")
colors.append("#CC6677")
colors.append("#882255")
colors.append("#AA4499")

darkgreen = "#006400"
darkblue = "#00008B"
crimson = "#DC143C"  # red
darkgoldenrod = "#B8860B"
goldenrod = "#DAA520"
darkcyan = "#008B8B"
forestgreen = "#228B22"
firebrick = "#B22222"
indianred = "#CD5C5C"

#==========================================
# Load data
#==========================================


dirResults = "/Users/christoph/Documents/PythonProjects/cm116988_clustersizeanalysis/cityControl/run/results/"

listSim = list()
listSimL = list()
listSimG = list()
listSimGL = list()
listSimIDA = list()
listSimPIDA = list()

listCoordAlgo = list()
listCoordAlgo.append("L")
listCoordAlgo.append("GL")
listCoordAlgo.append("G")
listCoordAlgo.append("IDA")
listCoordAlgo.append("PIDA")

listClusterSize = list()
listClusterSize.append(40)
listClusterSize.append(60)
listClusterSize.append(80)
listClusterSize.append(100)


for l in range(0, len(listCoordAlgo)):
	_coordAlgo = listCoordAlgo[l]
	for s in range(0, len(listClusterSize)):
		_size = listClusterSize[s]
		for root, dirs, files in os.walk(dirResults):
			# print(dirs)
			# 2015-03-11_12-19_startH-0_stepSize-900_shareRES-20_clusterSize-60_RSC-3_L_FINAL
			folderScenario = fnmatch.filter(dirs, '*_start*-0_*stepSize-900_shareRES-20_clusterSize-{}_RSC-3_{}_FINAL'.format(_size, _coordAlgo))
			if len(folderScenario) != 0:
				print folderScenario
				if _coordAlgo == "L":
					listSimL.append(folderScenario[0])
				elif _coordAlgo == "G":
					listSimG.append(folderScenario[0])
				elif _coordAlgo == "GL":
					listSimGL.append(folderScenario[0])
				elif _coordAlgo == "IDA":
					listSimIDA.append(folderScenario[0])
				elif _coordAlgo == "PIDA":
					listSimPIDA.append(folderScenario[0])
				else:
					print("Something went wrong")
					exit()


print listSimL
print listSimG
print listSimGL
print listSimGL
print listSimIDA
print listSimPIDA

#exit()

fig = plt.figure(figsize=(4, 2.5), dpi=300)
gs = mpl.gridspec.GridSpec(1, 1) # , height_ratios=[1, 1]
ax1 = plt.subplot(gs[0])

listPlots = list()
listPlotLegends = list()

for a in range(0, len(listCoordAlgo)):
	_coordAlgo = listCoordAlgo[a]
	annualAvgRPV = list()

	if _coordAlgo == "L":
		length = len(listSimL)
	elif _coordAlgo == "G":
		length = len(listSimG)
	elif _coordAlgo == "GL":
		length = len(listSimGL)
	elif _coordAlgo == "IDA":
		length = len(listSimIDA)
	elif _coordAlgo == "PIDA":
		length = len(listSimPIDA)

	for r in range(0, length):
		if _coordAlgo == "L":
			folderScenario = listSimL[r]
		elif _coordAlgo == "G":
			folderScenario = listSimG[r]
		elif _coordAlgo == "GL":
			folderScenario = listSimGL[r]
		elif _coordAlgo == "IDA":
			folderScenario = listSimIDA[r]
		elif _coordAlgo == "PIDA":
			folderScenario = listSimPIDA[r]

		# print(listSimL[r])
		fpath = dirResults + folderScenario + "/"
		
		# fluctuations = np.load(fpath + "fluctuations.npy")
		# fluctuations = fluctuations.T

		# remainders = np.load(fpath + "remainders.npy")
		# remainders = remainders.T

		performances = np.load(fpath + "performances.npy")
		if len(performances) != 365:
			print("Some invalid simulation run...")
			exit()
		_divisor = len(performances)
		annualRPV = np.sum(performances[:,1])
		annualAvgRPV.append(annualRPV/float(_divisor))
		# print(annualRPV)

	print(annualAvgRPV)


	datax = np.arange(0, length)
	datax = datax - 0.5 + 0.1/(len(listCoordAlgo)-1)
	print datax
	listPlots.append(ax1.bar(datax + 0.02 + (0.9/(len(listCoordAlgo))*a), annualAvgRPV, width = 0.72/len(listCoordAlgo), linewidth=0, color=colors[a]))
	if _coordAlgo == "L":
		legendTxt = "Uncoordinated"
	elif _coordAlgo == "G":
		legendTxt = "Central w/o local objectives"
	elif _coordAlgo == "GL":
		legendTxt = "Central w/ local objectives"
	elif _coordAlgo == "IDA":
		legendTxt = "IDA"
	elif _coordAlgo == "PIDA":
		legendTxt = "PIDA"

	listPlotLegends.append(legendTxt)
	#datax + 0.014 + (0.9/(len(listCoordAlgo))*a)

datax = np.arange(0, len(listClusterSize))
print datax
ax1.set_xticks(datax)
xlabel = listClusterSize
ax1.set_xticklabels(xlabel)
ax1.xaxis.set_tick_params(width=0.5, length=2)
ax1.set_xlim(-0.5, 3.5)


legendary = fig.legend(listPlots, listPlotLegends, loc='upper right', ncol=2)
legendary.get_frame().set_linewidth(0.5)
ax1.set_xlabel("Number of BES within cluster")
ax1.set_ylabel("Annual average RPV")
plt.subplots_adjust(left=0.12, bottom=0.15, right=0.995, top=0.84) # , right=1.0, top=1.0, wspace=0.001, hspace=0.001

fig.savefig("test.pdf")


	# ax1.plot(fluctuations[:,1])
	# ax1.plot(remainders[:,1])

	# fig.savefig(fpath + "results.pdf")

	#fluctuations2 = np.reshape(fluctuations, (fluctuations.shape[0]*fluctuations.shape[1],-1), order="F")

#remainder = np.load(dirResults + "remainders.npy")
#remainder = remainder.T
#remainder2 = np.reshape(remainder, (remainder.shape[0]*remainder.shape[1],-1), order="F")

#plt.plot(fluctuations2)
#plt.plot(remainder2)
#plt.plot(fluctuations2[0:96])

#plt.show()