__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

# set path
dirScript = os.path.dirname(__file__)
path = list()
path.append(dirScript + '/../_results_clustering_flexValue/FullYear_SortedDesync_new/performances.npy')
path.append(dirScript + '/../_results_clustering_flexValue/FullYear_SortedDesync_new_2/performances.npy')
path.append(dirScript + '/../_results_clustering_flexValue/FullYear_SortedDesync_new_3/performances.npy')   # change this!
veriNo = len(path)

markerR = 'o'
mc_R = 'lightcoral'
ms_R = 13
markerM = 'o'
mc_M = 'yellowgreen'
ms_M = 13

savePlot = True    # save file as pdf?
showPlot = True    # display plot?

noBes = 480

# fonts etc.
# ----------

bFigureType = "PDF"

pgf_with_custom_preamble = {
    "font.family": "serif", # use serif/main font for text elements
    "font.size": 16,
    "axes.labelsize": 16,
    "legend.fontsize": 12,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "lines.linewidth": 1,
    "axes.linewidth": 1,
    "pgf.rcfonts": False,   # don't setup fonts from rc parameters
    "pgf.preamble": [
         r"\usepackage{units}",         # load additional packages
         r"\usepackage{metalogo}",
         r"\usepackage{unicode-math}",  # unicode math setup
         r"\setmathfont{xits-math.otf}",
         # r"\setmainfont{ae}", # serif font via preamble
         ]
}

mpl.rcParams.update(pgf_with_custom_preamble)

# load results from given path
# ----------------------------

performances = np.zeros([veriNo, 2, 365, 4, 60])
for v in range(veriNo):
    performances[v] = np.load(path[v])

noDays = performances.shape[2]
noClusterSplittings = performances.shape[3]   # number of different cluster splittings

# create array that holds the number of members per cluster for each cluster splitting
noOfClusters = np.zeros(noClusterSplittings)
for s in range(noClusterSplittings):
    noOfClusters[s] = np.count_nonzero(performances[0,0,0,s])
noOfMembersPerClusterAvg = [noBes/noOfClusters[s] for s in range(noClusterSplittings)]   # this is the array mentioned above

compactnessAll = np.zeros([veriNo, 2, noDays, noClusterSplittings])
meanAll = np.zeros([veriNo, 2, noDays, noClusterSplittings])
for a in range(2):
    for h in range(noDays):
        for s in range(noClusterSplittings):
            for v in range(veriNo):
                performancesArrayTemp = [ performances[v, a, h, s, c] for c in range(int(noOfClusters[s])) ]
                meanAll[v, a, h, s] = np.mean(performancesArrayTemp)
                compactnessAll[v, a, h, s] =  np.sum( [ (meanAll[v, a, h, s] - performancesArrayTemp[c]) ** 2 for c in range(len(performancesArrayTemp)) ] ) / len(performancesArrayTemp)

compactnessRanAvgPerS = np.zeros([veriNo, noClusterSplittings])
compactnessManAvgPerS = np.zeros([veriNo, noClusterSplittings])
for v in range(veriNo):
    compactnessRanAvgPerS[v] = [ np.mean(compactnessAll[v, 0, :, s]) for s in range(noClusterSplittings) ]
    compactnessManAvgPerS[v] = [ np.mean(compactnessAll[v, 1, :, s]) for s in range(noClusterSplittings) ]

xAxis = np.arange(noClusterSplittings)

# create subplots
fig, ax = plt.subplots()

plots = []
plots_legend = []

#for v in range(veriNo):
plots_legend.append('Random clustering')
plots_legend.append('Managed clustering')

plots.append(ax.plot(xAxis-0.15, compactnessRanAvgPerS[0,::-1], markerR, markersize=ms_R, color=mc_R)[0])
plots.append(ax.plot(xAxis+0.00, compactnessRanAvgPerS[1,::-1], markerR, markersize=ms_R, color=mc_R)[0])
plots.append(ax.plot(xAxis+0.15, compactnessRanAvgPerS[2,::-1], markerR, markersize=ms_R, color=mc_R)[0])

plots.append(ax.plot(xAxis-0.15, compactnessManAvgPerS[0,::-1], markerM, markersize=ms_M, color=mc_M)[0])
plots.append(ax.plot(xAxis+0.00, compactnessManAvgPerS[1,::-1], markerM, markersize=ms_M, color=mc_M)[0])
plots.append(ax.plot(xAxis+0.15, compactnessManAvgPerS[2,::-1], markerM, markersize=ms_M, color=mc_M)[0])




legend = fig.legend([plots[0], plots[veriNo]], plots_legend, loc='upper center', ncol=2, numpoints=1)


# labeling etc
# ------------

ax.set_ylabel('Compactness', labelpad=20)
ax.set_xlabel(r'$\varnothing$' + ' Number of BESs per cluster /\nNumber of clusters', labelpad=20)

ax.set_xlim([-0.5,3.5])
ax.set_xticks(xAxis)
ax.set_xticklabels( ('8 / 60', '16 / 30', '24 / 20', '32 / 15') )

xAxis2 = np.array([0-0.15,0,0+0.15, 1-0.15,1,1+0.15, 2-0.15,2,2+0.15, 3-0.15,3,3+0.15])
ax2 = ax.twiny()
ax2.set_xlim([-0.5,3.5])
ax2.set_xticks(xAxis2)
ax2.set_xticklabels(('1', '2', '3', '1', '2', '3', '1', '2', '3', '1', '2', '3'))
ax2.set_xlabel('Scenario No.', labelpad=20)

ax.yaxis.grid()

fig.patch.set_facecolor('white')
fig.subplots_adjust(top=0.8, bottom=0.175, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/fig_SIM_verification_compactness"
    fig.savefig(fig_name + ".pdf")