__author__ = 'christoph'

bFigureType = "PDF"

import numpy as np
import matplotlib as mpl

if bFigureType == "PGF":
    mpl.use('pgf')

showPlot = True
savePlot = True
name = "fig_EC"


pgf_with_custom_preamble = {
    "font.family": "serif", # use serif/main font for text elements
    "font.size": 7,
    "axes.labelsize": 7,
    "legend.fontsize": 6,
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

width = 4.0  # in inches
height = 2.0
# Plot the data
fig, ax = plt.subplots(dpi=300, figsize=(width, height), nrows=1, ncols=3, sharex=True, sharey=True)

#plt.subplots_adjust(left=0.2, bottom=None, right=0.9, top=0.8, wspace=0.001, hspace=0.001)
#print fig.get_size_inches()

# set figure's color
fig.patch.set_facecolor('white')

plot1 = ax[0].bar(time, fluc, linewidth=0.5, color='lightskyblue')
ax[0].set_xlim(time[0], time[-1]+1.0)
ax[0].set_ylim(min(min(fluc), min(delta), min(cumsum))*1.05, max(max(fluc), max(delta), max(cumsum))*1.05)
ax[0].get_yaxis().set_ticks([0])
ax[0].xaxis.set_tick_params(width=0.5, length=2)
ax[0].axhline(0, color='black')
#img = ax[0,1].bar(time, fluc)
plot2, = ax[0].plot(average, color='#000000')  # the comma behind plot2 causes that only the first argument is taken which is needed for the legend
plot3 = ax[1].bar(time, delta, linewidth=0.5, color='yellowgreen')

ax[1].xaxis.set_tick_params(width=0.5, length=2)
ax[1].axhline(0, color='black')

barColors4 = ['darkorange' for t in range(len(fluc))]
maxIndex = np.argmax(cumsum)
barColors4[maxIndex] = 'gold'
plot4 = ax[2].bar(time, cumsum, linewidth=0.5, color=barColors4)
ax[2].xaxis.set_tick_params(width=0.5, length=2)
ax[2].axhline(0, color='black')

ax[0].set_xlabel("Time t")
ax[1].set_xlabel("Time t")
ax[2].set_xlabel("Time t")
ax[0].set_ylabel("Energy")

test = fig.legend((plot1, plot2, plot3, plot4), ('Fluctuations', 'Average of fluctuations', 'Shifted fluctuations', 'Cumulative sum of shifted fluctuations'), 'upper center', ncol=2)
test.get_frame().set_linewidth(0)

fig.subplots_adjust(top=0.8, bottom=0.2, left=0.1, right=0.9, hspace=0.02, wspace=0.02)

offset = 0.01
xleft = ax[0].get_position().x0 + offset
ytop = ax[0].get_position().y1 - offset

xleft = ax[1].get_position().x0 + offset
ytop = ax[1].get_position().y1 - offset

xleft = ax[2].get_position().x0 + offset
ytop = ax[2].get_position().y1 - offset


fig_name = os.path.basename(__file__)[:-9] + "fig"

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/" + name
    fig.savefig(fig_name + ".pdf")
