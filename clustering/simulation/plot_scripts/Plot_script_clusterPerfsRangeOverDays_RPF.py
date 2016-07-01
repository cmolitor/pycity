__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

# set path
dirScript = os.path.dirname(__file__)
path = dirScript + '/../_results_clustering_flexValue/2014-11-27_23-56/Balancing-Performance_NoBes-300_ClMin-10_ClMax-60_ClSplittings-7_rSeed-17_StartH-130_Horizons-7_h-136.npy'

savePlot = True    # save file as pdf?
showPlot = False    # display plot?
noBes = 300         # no of BES (manually update this for correct numbers of BESs per cluster)
markerR = 'ro'      # marker style for results of random clustering
markerP = 'g_'      # marker style for results of balanced clustering
markerF = 'b^'      # marker style for results of balanced clustering
ms_R = 4            # marker size for results of random clustering
ms_P = 4            # marker size for results of balanced clustering
ms_F = 4            # marker size for results of balanced clustering
width = 6.0         # in inches
height = 6.0        # in inches
noOfYTicks = 4      # number of ticks on y axis of each subplot
plotNomPowCl = False
# fonts etc.
# ----------

bFigureType = "PDF"

pgf_with_custom_preamble = {
    "font.family": "serif", # use serif/main font for text elements
    "font.size": 8,
    "axes.labelsize": 6,
    "legend.fontsize": 6,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "lines.linewidth": 0.5,
    "axes.linewidth": 0.5,
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

results = np.load(path)
scenario_name = os.path.splitext(os.path.basename(path))[0]
scenario_name = scenario_name.replace(".", "-")
fig_name = "fig_{}".format(scenario_name)

noDays = results.shape[1]
noClusterSplitting = results.shape[2]   # number of different cluster splittings

# create array that holds the number of members per cluster for each cluster splitting
noOfClusters = np.zeros(noClusterSplitting)
for s in range(noClusterSplitting):
    noOfClusters[s] = np.count_nonzero(results[0,0,s])
noOfMembersPerClusterAvg = [noBes/noOfClusters[s] for s in range(noClusterSplitting)]   # this is the array mentioned above

# create subplots
fig, ax = plt.subplots(dpi=200, figsize=(width, height), nrows=noClusterSplitting, ncols=1, sharex=True, sharey=False)

# set properties of all subplots' axes
for s in range(noClusterSplitting):
    ax[s].get_xaxis().set_ticks(np.arange(0, noDays+1, 1))  # only show x-ticks for existing data sets
    ax[s].xaxis.set_tick_params(width=0, length=0)          # no lines for ticks
    ax[s].set_xlim([0, noDays+1])                           # set x axis range (leave some space at beginning and end)

    yLim = float(np.ceil(2*max(results[:, :, s, :].flatten())))/2.
    ax[s].yaxis.labelpad = 30
    ax[s].yaxis.set_label_position("right")
    ax[s].get_yaxis().set_ticks([yLim/noOfYTicks*x for x in range(1, noOfYTicks+1)  ])
    ax[s].xaxis.set_tick_params(width=0, length=0)
    ax[s].set_ylim([0, yLim])
    ax[s].set_ylabel("{} BES\nper Cluster".format(noOfMembersPerClusterAvg[s]), rotation='horizontal')

    ax[s].yaxis.grid()

# set labels
ax[0].set_title("Range of Performances of Clusters\n")                                                       # title
fig.text(0.5, 0.05, 'Day', ha='center', va='center', rotation='horizontal')                         # x
fig.text(0.05, 0.5, 'Relative Energy Criterion (Max & Min)', ha='center', va='center', rotation='vertical')     # y

# set legend
markerSymbolR, = mpl.pyplot.plot(0, markerR, markersize=ms_R)
if plotNomPowCl:
    markerSymbolP, = mpl.pyplot.plot(0, markerP, markersize=ms_P)
markerSymbolF, = mpl.pyplot.plot(0, markerF, markersize=ms_F)
if plotNomPowCl:
    plt.figlegend([markerSymbolR, markerSymbolP, markerSymbolF], ["Random Clustering", "NomPower Clustering", "Flexibility Clustering"], loc='upper right')
else:
    plt.figlegend([markerSymbolR, markerSymbolF], ["Random Clustering", "Flexibility Clustering"], loc='upper right', numpoints=1, ncol=1)

# set figure's color
fig.patch.set_facecolor('white')

# manipulate data so that none of the zero values will be shown in plot
results[results == 0] = -1

# plot data
xAxis = [x for x in range(1, noDays+1)]
xAxisL = [x-0.1 for x in range(1, noDays+1)]
xAxisR = [x+0.1 for x in range(1, noDays+1)]
for s in range(noClusterSplitting):
    # get max and min performances for each day for random clustering
    data = [ [ min(results[0, h, s, 0:noOfClusters[s]]), max(results[0, h, s, 0:noOfClusters[s]]) ]  for h in range(noDays) ]
    plot1 = ax[s].plot(xAxisL, data, markerR, label='plot1', markersize=ms_R)
    # get max and min performances for each day for Nom Power clustering
    if plotNomPowCl:
        data = [ [ min(results[1, h, s, 0:noOfClusters[s]]), max(results[1, h, s, 0:noOfClusters[s]]) ]  for h in range(noDays) ]
        plot2 = ax[s].plot(xAxisR, data, markerP, label='plot2', markersize=ms_P)
    # get max and min performances for each day for flexibility clustering
    data = [ [ min(results[2, h, s, 0:noOfClusters[s]]), max(results[2, h, s, 0:noOfClusters[s]]) ]  for h in range(noDays) ]
    plot3 = ax[s].plot(xAxis, data, markerF, label='plot3', markersize=ms_F)

fig.subplots_adjust(top=0.85, bottom=0.15, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(path) + "/fig_perfsRangesOverDays"
    fig.savefig(fig_name + ".pdf")

