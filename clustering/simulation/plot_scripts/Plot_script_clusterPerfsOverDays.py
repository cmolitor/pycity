__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

# set path
dirScript = os.path.dirname(__file__)
path = dirScript + '/../_results_clustering_flexValue/2014-12-06_00-17/performances_480BES_4ClS_92Days_Start273-_h-364.npy'

showPlot = False
savePlot = True    # save file as pdf?
noBes = 480         # no of BES (manually update this for correct numbers of BESs per cluster)
markerR = 'r_'      # marker style for results of random clustering
markerB = 'g_'      # marker style for results of balanced clustering
ms_R = 5            # marker size for results of random clustering
ms_B = 5            # marker size for results of balanced clustering
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
    "ytick.labelsize": 6,
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
    ax[s].set_ylabel("{:.2f} BES\nper Cluster".format(noOfMembersPerClusterAvg[s]), rotation='horizontal')

    ax[s].yaxis.grid()

# set labels
ax[0].set_title("Performances of Clusters\n")                                                       # title
fig.text(0.5, 0.05, 'Day', ha='center', va='center', rotation='horizontal')                         # x
fig.text(0.05, 0.5, 'Relative Energy Criterion', ha='center', va='center', rotation='vertical')     # y

# set legend
markerSymbolR, = mpl.pyplot.plot(0, markerR, markersize=ms_R)
markerSymbolB, = mpl.pyplot.plot(0, markerB, markersize=ms_B)
plt.figlegend([markerSymbolR, markerSymbolB], ["Random Clustering", "Controlled Clustering"], loc='upper right', numpoints=1, ncol=1)

# set figure's color
fig.patch.set_facecolor('white')

# manipulate data so that none of the zero values will be shown in plot
results[results == 0] = -1

# plot data
xAxisL = [x-0.1 for x in range(1, noDays+1)]
xAxisR = [x+0.1 for x in range(1, noDays+1)]
for s in range(noClusterSplitting):
    plot1 = ax[s].plot(xAxisL, results[0, :, s, :], markerR, label='plot1', markersize=ms_R)
    plot2 = ax[s].plot(xAxisR, results[1, :, s, :], markerB, label='plot2', markersize=ms_B)

fig.subplots_adjust(top=0.85, bottom=0.15, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(path) + "/fig_perfsOverDays"
    fig.savefig(fig_name + ".pdf")


