__author__ = 'christoph'

bFigureType = "PDF"

import numpy as np
import matplotlib as mpl
from pylab import *


showPlot = True
savePlot = True    # save file as pdf?
name = "fig_flexibilityDesiredDiff_2"

if bFigureType == "PGF":
    mpl.use('pgf')

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

import matplotlib.pyplot as plt
import os
import fnmatch

#flexs = np.array([65, 40, 45, 90])
flexs = np.array([65, 60, 45, 70])
#flexs = np.array([65, 60, 55, 60])

avgF = np.array([np.mean(flexs) for x in range(len(flexs)+1)])

# Plot the data
fig, ax = plt.subplots()

# set figure's color
fig.patch.set_facecolor('white')

ind = np.arange(4)
width = 0.5

plot1 = ax.bar(ind, flexs, width=width, color='yellowgreen')

diff = min(abs(avgF[0]-min(flexs)), abs(avgF[0]-max(flexs)))

arr1 = Arrow(np.argmin(flexs)+0.25, min(flexs), 0, diff, color='darkgreen', width=0.2)
arr2 = Arrow(np.argmax(flexs)+0.25, max(flexs), 0, -diff, color='darkgreen', width=0.2)
ax.add_patch(arr1)
ax.add_patch(arr2)

ax.set_xticks(ind+width/2)
ax.set_xticklabels( ('1', '2', '3', '4') )
ax.set_xlim([0,3.5])

ax.set_yticks(np.arange(11)*10)
ax.set_ylim([0,100])

ax.xaxis.set_tick_params(width=0, length=0)
plot3, = ax.plot(avgF, color='#000000', linewidth=3)  # the comma behind plot2 causes that only the first argument is taken which is needed for the legend

ax.set_xlabel("Cluster", labelpad=20)
ax.set_ylabel("Flexibility", labelpad=20)

ax.yaxis.grid()


test = fig.legend((plot1, arr1, plot3), ('Accumulated Flexibility', 'Desired difference', 'Average flexibility'), 'upper center', ncol=3)

fig.subplots_adjust(top=0.85, bottom=0.125, left=0.15, right=0.85, hspace=0.02, wspace=0.02)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/" + name
    fig.savefig(fig_name + ".pdf")
