__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

# set path
dirScript = os.path.dirname(__file__)
pathMulti = dirScript + '/../_results_clustering_multiDSync/multiDSync_days-365_RES-020/performances_8ClS_365Days_Start0-_h-362.npy'
pathSorted = dirScript + '/../_results_clustering_sortedDSync/sortedDSync_days-365_RES-020/performances_8ClS_365Days_Start0-_h-362.npy'
multiDesync = np.load(pathMulti)
sortedDesync = np.load(pathSorted)



savePlot = True    # save file as pdf?
showPlot = False    # display plot?
#noBes = 480         # no of BES (manually update this for correct numbers of BESs per cluster)
markerR = 'r-'      # marker style for results of random clustering
markerB = 'g-'      # marker style for results of balanced clustering
ms_R = 2            # marker size for results of random clustering
ms_B = 2            # marker size for results of balanced clustering
width = 10.0         # in inches
height = 6.0        # in inches
noOfYTicks = 4      # number of ticks on y axis of each subplot

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


fig_name = "fig_DeSyncComparison"

noDays = multiDesync.shape[0]
noClusterSplitting = multiDesync.shape[1]   # number of different cluster splittings

# create array that holds the number of members per cluster for each cluster splitting
noOfMembersInCluster = np.zeros(noClusterSplitting)
for s in range(noClusterSplitting):
    noOfMembersInCluster[s] = np.count_nonzero(multiDesync[0,s])

# create subplots
fig, ax = plt.subplots(dpi=200, figsize=(width, height), nrows=noClusterSplitting, ncols=1, sharex=True, sharey=False)

# set properties of all subplots' axes
for s in range(noClusterSplitting):
    ax[s].get_xaxis().set_ticks(np.arange(0, noDays+1, 1))  # only show x-ticks for existing data sets
    ax[s].xaxis.set_tick_params(width=0, length=0)          # no lines for ticks
    ax[s].set_xlim([0, noDays+1])                           # set x axis range (leave some space at beginning and end)

    yLim = float(np.ceil(2*max(multiDesync[:, s, :].flatten())))/2.
    ax[s].yaxis.labelpad = 30
    ax[s].yaxis.set_label_position("right")
    ax[s].get_yaxis().set_ticks([yLim/noOfYTicks*x for x in range(1, noOfYTicks+1)  ])
    ax[s].xaxis.set_tick_params(width=0, length=0)
    ax[s].set_ylim([0, yLim])
    ax[s].set_ylabel("{} BES\nper Cluster".format(noOfMembersInCluster[s]), rotation='horizontal')

    ax[s].yaxis.grid()

# set labels
ax[0].set_title("Range of Performances of Clusters\n")                                                       # title
fig.text(0.5, 0.05, 'Day', ha='center', va='center', rotation='horizontal')                         # x
fig.text(0.05, 0.5, 'Relative Energy Criterion (Max & Min)', ha='center', va='center', rotation='vertical')     # y

# set legend
markerSymbolR, = mpl.pyplot.plot(0, markerR, markersize=ms_R)
markerSymbolB, = mpl.pyplot.plot(0, markerB, markersize=ms_B)
plt.figlegend([markerSymbolR, markerSymbolB], ["Random Clustering", "Controlled Clustering"], loc='upper right', numpoints=1, ncol=1)

# set figure's color
fig.patch.set_facecolor('white')

# manipulate data so that none of the zero values will be shown in plot
multiDesync[multiDesync == 0] = -1

# plot data
xAxis = range(1, noDays+1)
for s in range(noClusterSplitting):
    # get max and min performances for each day for random clustering
    data = [ [ min(multiDesync[h, s, 0:noOfMembersInCluster[s]]), max(multiDesync[h, s, 0:noOfMembersInCluster[s]]) ]  for h in range(noDays) ]
    plot1 = ax[s].plot(xAxis, data, markerR, label='plot1', markersize=ms_R)
    # get max and min performances for each day for controlled clustering
    data = [ [ sortedDesync[h, s] ]  for h in range(noDays) ]
    plot2 = ax[s].plot(xAxis, data, markerB, label='plot2', markersize=ms_B)

    data = [ [ np.mean(multiDesync[h, s, 0:noOfMembersInCluster[s]]) ] for h in range(noDays) ]
    plot3 = ax[s].plot(xAxis, data, 'b-', label='plot3', markersize=ms_R)

fig.subplots_adjust(top=0.85, bottom=0.15, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/fig_DesyncComparison"
    fig.savefig(fig_name + ".pdf")

