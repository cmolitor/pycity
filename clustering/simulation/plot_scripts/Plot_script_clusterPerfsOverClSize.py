__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

# set path
dirScript = os.path.dirname(__file__)
path = dirScript + '/../_results_clustering_flexValue/2014-11-21_16-06/Balancing-Performance_NoBes-150_ClMin-8_ClMax-30_ClSplittings-4_rSeed-4_Horizons-14.npy'

savePlot = True    # save file as pdf?
showPlot = False    # display plot?
noBes = 150         # no of BES (manually update this for correct numbers of BESs per cluster)
day = 3             # index of day to be plotted
# nice: 0,1,3,8,10,13
markerR = '+'      # marker style for results of random clustering
markerB = 'o'      # marker style for results of balanced clustering
ms_R = 3           # marker size for results of random clustering
ms_B = 3            # marker size for results of balanced clustering
width = 3.15         # in inches
height = 2.0        # in inches


colors =[]
colors.append("#332288")
colors.append("#88CCEE")
colors.append("#44AA99")
colors.append("#117733")
colors.append("#999933")
colors.append("#DDCC77")
colors.append("#CC6677")
colors.append("#882255")
colors.append("#AA4499")

# fonts etc.
# ----------

bFigureType = "PDF"

pgf_with_custom_preamble = {
    "font.family": "serif", # use serif/main font for text elements
    "font.size": 8,
    "axes.labelsize": 7,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "lines.linewidth": 1,
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

noClusterSplitting = results.shape[2]   # number of different cluster splittings

# create array that holds the number of members per cluster for each cluster splitting
noOfClusters = np.zeros(noClusterSplitting)
for s in range(noClusterSplitting):
    noOfClusters[s] = np.count_nonzero(results[0,0,s])
noOfMembersPerClusterAvg = [noBes/noOfClusters[s] for s in range(noClusterSplitting)]   # this is the array mentioned above

# create (single) subplot
fig, ax = plt.subplots(dpi=200, figsize=(width, height), nrows=1, ncols=1, sharex=True, sharey=True)

# set properties of axes
ax.get_xaxis().set_ticks(noOfMembersPerClusterAvg)      # only show x-ticks for existing data sets
ax.get_yaxis().set_ticks(np.arange(0, max(results[:, day, :, :].flatten())+0.1, 0.2 ))  # step size of 0.1 for y
ax.xaxis.set_tick_params(width=0, length=0)     # no lines for ticks
ax.yaxis.set_tick_params(width=0, length=0)     # no lines for ticks
ax.set_xlim([noOfMembersPerClusterAvg[-1]-1, noOfMembersPerClusterAvg[0]+1])    # set x axis range (leave some space at beginning and end)
ax.set_ylim([0, max(results[:, day, :, :].flatten())+0.1])                      # set y axis range

# set labels
#ax.set_title("Performances of Clusters\n")          # title
ax.set_ylabel("REC")          # y
ax.yaxis.labelpad = 10
ax.set_xlabel("Avg. number of members per cluster") # x
ax.xaxis.labelpad = 10
# set legend
#markerSymbolR, = mpl.pyplot.plot(0, markerR, markersize=ms_R)
#markerSymbolB, = mpl.pyplot.plot(0, markerB, markersize=ms_B)
#plt.legend([markerSymbolR, markerSymbolB], ["Random Clustering", "Controlled Clustering"])

# set figure's color
fig.patch.set_facecolor('white')

# manipulate data so that none of the zero values will be shown in plot
results[results == 0] = -1

# plot data
xAxis = np.array([noOfMembersPerClusterAvg[x] for x in range(noClusterSplitting)])
plots = []
plots_legend = []
plots.append(ax.plot(xAxis-0.1, results[1, day, :, :], markerB, label='plot2', markersize=ms_B, markerfacecolor='None', markeredgecolor=colors[0], markeredgewidth=0.4)[0])
plots_legend.append('Balanced clusters')
plots.append(ax.plot(xAxis+0.1, results[0, day, :, :], markerR, label='plot1', markersize=ms_R, markerfacecolor='None', markeredgecolor=colors[7], markeredgewidth=0.4)[0])
plots_legend.append('Random clusters')
fig.subplots_adjust(top=0.99, bottom=0.2, left=0.15, right=0.995)
legend = fig.legend(plots, plots_legend, loc='upper right', ncol=1, numpoints=1)
legend.get_frame().set_linewidth(0.0)


ax.yaxis.grid(linewidth=0.2)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(path) + "/fig_perfOverClSize_day-{}".format(day)
    fig.savefig(fig_name + ".pdf")