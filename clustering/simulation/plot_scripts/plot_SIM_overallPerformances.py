__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

# set path
dirScript = os.path.dirname(__file__)
path = dirScript + '/../_results_clustering_flexValue/FullYear_SortedDesync_new/overall.npy'

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

overallPerformances = np.load(path)

noDays = overallPerformances.shape[1]
noClusterSplittings = overallPerformances.shape[2]   # number of different cluster splittings

overallPerformancesRanAvgPerS = [ np.mean(overallPerformances[0, :, s]) for s in range(noClusterSplittings) ]
overallPerformancesManAvgPerS = [ np.mean(overallPerformances[1, :, s]) for s in range(noClusterSplittings) ]

ind = np.arange(noClusterSplittings)
width = 0.33

# create subplots
#fig, ax = plt.subplots(dpi=200, figsize=(width, height) sharex=True, sharey=False)
fig, ax = plt.subplots()

rectsRan = ax.bar(ind, overallPerformancesRanAvgPerS[::-1] , width, color='gold')
rectsMan = ax.bar(ind+width, overallPerformancesManAvgPerS[::-1] , width, color='darkorange')

# labeling etc
# ------------

ax.set_ylabel('Overall REC', labelpad=20)
ax.set_xlabel(r'$\varnothing$' + ' Number of BESs per cluster /\nNumber of clusters', labelpad=20)

ax.set_xticks(ind+width)
ax.set_xticklabels( ('8 / 60', '16 / 30', '24 / 20', '32 / 15') )
ax.set_xlim([0-width, max(ind)+1])

ax.yaxis.grid()

test = fig.legend((rectsRan, rectsMan), ('Random clustering', 'Managed Clustering'), 'upper center', ncol=2)

fig.patch.set_facecolor('white')
fig.subplots_adjust(top=0.85, bottom=0.175, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/fig_SIM_overallPerformances_Random-Managed"
    fig.savefig(fig_name + ".pdf")