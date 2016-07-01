__author__ = 'christoph'

bFigureType = "PDF"

import numpy as np
import matplotlib as mpl

showPlot = True
savePlot = True    # save file as pdf?
name = "fig_CHP-HP-operation"

if bFigureType == "PGF":
    mpl.use('pgf')

pgf_with_custom_preamble = {
    "font.family": "serif", # use serif/main font for text elements
    "font.size": 7,
    "axes.labelsize": 7,
    "legend.fontsize": 7,
    "xtick.labelsize": 5,
    "ytick.labelsize": 5,
    "lines.linewidth": 0.5,
    "axes.linewidth": 0.5,
    "text.usetex": True,    # use inline math for ticks
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

fluc = np.array([33165425.9009, 23874440.0216, 19122885.4946, 17457720.4044, 16428923.8114, 16386499.2449, 17372870.9291, 21212296.9344, 37556371.6128, 58758061.892, 73893035.741, 86026469.2862, 87691634.7188, 73405152.5418, 57750477.9246, 44467076.0128, 40267041.1924, 44327713.959, 62352064.4274, 74783952.3218 ,67932380.727, 57495930.5257, 48682221.1906, 35901811.8083])

time = np.array([x for x in range(0, len(fluc))])
average = np.array([np.mean(fluc) for x in range(0, len(fluc)+1)])
delta = average[0:-1] - fluc
cumsum = np.cumsum(delta)

width = 3.0  # in inches
height = 2.0
# Plot the data
fig, ax = plt.subplots(dpi=300, figsize=(width, height), nrows=1, ncols=1, sharex=True, sharey=False)

#plt.subplots_adjust(left=0.2, bottom=None, right=0.9, top=0.8, wspace=0.001, hspace=0.001)
#print fig.get_size_inches()

# set figure's color
fig.patch.set_facecolor('white')

barColors = ['lightskyblue' for t in range(len(fluc))]
for b in range(len(fluc)):
    if fluc[b] > average[0]:
        barColors[b] = 'darkorange'

plot1 = ax.bar(time, fluc, linewidth=0.5, color=barColors)
ax.set_xlim(time[0], time[-1]+1.0)
ax.set_ylim(0, max(fluc)*1.05)
ax.get_yaxis().set_ticks([0])
ax.xaxis.set_tick_params(width=0.5, length=2)
ax.axhline(0, color='black')
#img = ax[0,1].bar(time, fluc)
plot2, = ax.plot(average, color='#000000', linewidth=0.7)  # the comma behind plot2 causes that only the first argument is taken which is needed for the legend

ax.set_xlabel("Time in hours")
ax.set_ylabel("Energy")

test = fig.legend((plot2,), ('Average of fluctuations',), 'upper center', ncol=2)
test.get_frame().set_linewidth(0)

fig.subplots_adjust(top=0.85, bottom=0.15, left=0.15, right=0.85, hspace=0.02, wspace=0.02)

fig_name = os.path.basename(__file__)[:-9] + "fig"

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/" + name
    fig.savefig(fig_name + ".pdf")
