__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

# set path
dirScript = os.path.dirname(__file__)
path = dirScript + '/../_results_clustering_flexValue/FullYear_SortedDesync_new_4_stages/performances.npy'

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

performances = np.load(path)[:, :, :, :, ]

noDays = performances.shape[1] #change
noClusterSplittings = performances.shape[2]   # number of different cluster splittings

# create array that holds the number of members per cluster for each cluster splitting
noOfClusters = np.zeros(noClusterSplittings)
for s in range(noClusterSplittings):
    noOfClusters[s] = np.count_nonzero(performances[0,0,s])
noOfMembersPerClusterAvg = [noBes/noOfClusters[s] for s in range(noClusterSplittings)]   # this is the array mentioned above

compactnessAll = np.zeros([4, noDays, noClusterSplittings])
meanAll = np.zeros([4, noDays, noClusterSplittings])
for a in range(4):
    for h in range(noDays):
        for s in range(noClusterSplittings):
            performancesArrayTemp = [ performances[a, h, s, c] for c in range(int(noOfClusters[s])) ]
            meanAll[a, h, s] = np.mean(performancesArrayTemp)
            compactnessAll[a, h, s] =  np.sum( [ (meanAll[a, h, s] - performancesArrayTemp[c]) ** 2 for c in range(len(performancesArrayTemp)) ] ) / len(performancesArrayTemp)

compactnessRanAvgPerS = [ np.mean(compactnessAll[0, :, s]) for s in range(noClusterSplittings) ]
compactnessTypAvgPerS = [ np.mean(compactnessAll[1, :, s]) for s in range(noClusterSplittings) ]
compactnessPowAvgPerS = [ np.mean(compactnessAll[2, :, s]) for s in range(noClusterSplittings) ]
compactnessFleAvgPerS = [ np.mean(compactnessAll[3, :, s]) for s in range(noClusterSplittings) ]

ind = np.arange(noClusterSplittings)
width = 0.2

# create subplots
fig, ax = plt.subplots()

rectsRan = ax.bar(ind+0*width, compactnessRanAvgPerS[::-1] , width, color='lightcoral')
rectsTyp = ax.bar(ind+1*width, compactnessTypAvgPerS[::-1] , width, color='gold')
rectsPow = ax.bar(ind+2*width, compactnessPowAvgPerS[::-1] , width, color='lightskyblue')
rectsFle = ax.bar(ind+3*width, compactnessFleAvgPerS[::-1] , width, color='yellowgreen')

# labeling etc
# ------------

ax.set_ylabel('Compactness', labelpad=20)
ax.set_xlabel(r'$\varnothing$' + ' Number of BESs per cluster /\nNumber of clusters', labelpad=20)

ax.set_xticks(ind+2*width)
ax.set_xticklabels( ('8 / 60', '16 / 30', '24 / 20', '32 / 15') )
ax.set_xlim([0-width, max(ind)+1])

ax.yaxis.grid()

test = fig.legend((rectsRan, rectsTyp, rectsPow, rectsFle), ('Clustering randomly', 'Clustering by type', 'Clustering by type & by power', 'Clustering by type & by power & by flexibility'), 'upper center', ncol=2)

fig.patch.set_facecolor('white')
fig.subplots_adjust(top=0.85, bottom=0.175, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/fig_SIM_compactness_steps_Random-Managed"
    fig.savefig(fig_name + ".pdf")