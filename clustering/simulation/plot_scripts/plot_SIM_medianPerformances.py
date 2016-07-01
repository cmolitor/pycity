__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

# set path
dirScript = os.path.dirname(__file__)
path = dirScript + '/../_results_clustering_flexValue/FullYear_SortedDesync_new/performances.npy'

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

performances = np.load(path)

noDays = performances.shape[1]
noClusterSplittings = performances.shape[2]   # number of different cluster splittings

# create array that holds the number of members per cluster for each cluster splitting
noOfClusters = np.zeros(noClusterSplittings)
for s in range(noClusterSplittings):
    noOfClusters[s] = np.count_nonzero(performances[0,0,s])
noOfMembersPerClusterAvg = [noBes/noOfClusters[s] for s in range(noClusterSplittings)]   # this is the array mentioned above

medianAll = np.zeros([2, noDays, noClusterSplittings])
for a in range(2):
    for h in range(noDays):
        for s in range(noClusterSplittings):
            performancesArrayTemp = [ performances[a, h, s, c] for c in range(int(noOfClusters[s])) ]
            medianAll[a, h, s] = np.median(performancesArrayTemp)

medianRanPerS = [ np.mean(medianAll[0, :, s]) for s in range(noClusterSplittings) ]
medianManPerS = [ np.mean(medianAll[1, :, s]) for s in range(noClusterSplittings) ]

ind = np.arange(noClusterSplittings)
width = 0.35

# create subplots
#fig, ax = plt.subplots(dpi=200, figsize=(width, height) sharex=True, sharey=False)
fig, ax = plt.subplots()

rectsRan = ax.bar(ind, medianRanPerS, width, color='lightcoral')
rectsMan = ax.bar(ind+width, medianManPerS, width, color='yellowgreen')

# labeling etc
# ------------

ax.set_ylabel('Median REC\n(Average over 365 days)', labelpad=20)
ax.set_xlabel('Number of BESs', labelpad=20)

ax.set_xticks(ind+width)
ax.set_xticklabels( ('8', '16', '24', '32') )

ax.yaxis.grid()

test = fig.legend((rectsRan, rectsMan), ('Random clustering', 'Managed Clustering'), 'upper center', ncol=2)

fig.patch.set_facecolor('white')
fig.subplots_adjust(top=0.85, bottom=0.15, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/fig_SIM_medianPerformances_Random-Managed"
    fig.savefig(fig_name + ".pdf")