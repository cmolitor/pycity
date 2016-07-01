__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

# set path
dirScript = os.path.dirname(__file__)

savePlot = True    # save file as pdf?
showPlot = True    # display plot?
marker = 'o'      # marker style for results of balanced clustering
ms = 15            # marker size for results of balanced clustering

name = "fig_compactnessExample"

# fonts etc.
# ----------

bFigureType = "PDF"

pgf_with_custom_preamble = {
    "font.family": "serif", # use serif/main font for text elements
    "font.size": 20,
    "axes.labelsize": 20,
    "legend.fontsize": 16,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
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

data = [[0.2, 0.4, 0.6, 0.8], [0.3, 0.4, 0.6, 0.7]]

mean1 = np.mean(data[0])
mean2 = np.mean(data[1])
compactness1 = np.sum( [ (mean1 - data[0][c]) ** 2 for c in range(len(data[0])) ] ) / len(data[0])
compactness2 = np.sum( [ (mean2 - data[1][c]) ** 2 for c in range(len(data[1])) ] ) / len(data[1])
print compactness1
print compactness2
print "mean1:", mean1
print "mean2:", mean2

# create (single) subplot
fig, ax = plt.subplots()

# set properties of axes
ax.set_xticks([1,2])
ax.set_xticklabels( ('Clustering 1', 'Clustering 2') )

for tick in ax.get_xaxis().get_major_ticks():
    tick.set_pad(20)
    tick.label1 = tick._get_text1()

ax.set_yticks([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1])

ax.xaxis.set_tick_params(width=0, length=0)     # no lines for ticks
ax.yaxis.set_tick_params(width=0, length=0)     # no lines for ticks

ax.set_xlim([0.5, 2.5])    # set x axis range (leave some space at beginning and end)
ax.set_ylim([0, 1])                      # set y axis range

# set labels
#ax.set_title("Performances of Clusters\n")          # title
ax.set_ylabel("REC", labelpad=20)          # y
# set legend
#markerSymbolR, = mpl.pyplot.plot(0, markerR, markersize=ms_R)
#markerSymbolB, = mpl.pyplot.plot(0, markerB, markersize=ms_B)
#plt.legend([markerSymbolR, markerSymbolB], ["Random Clustering", "Controlled Clustering"])

# set figure's color
fig.patch.set_facecolor('white')
ax.yaxis.grid()

# plot data
xAxis = np.array([1, 2])
plots = []
plots_legend = []
plots.append(ax.plot(xAxis, data, marker, label='plot2', markersize=ms, color='yellowgreen')[0])

fig.subplots_adjust(top=0.9, bottom=0.1, left=0.15, right=0.85)


if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/" + name
    fig.savefig(fig_name + ".pdf")