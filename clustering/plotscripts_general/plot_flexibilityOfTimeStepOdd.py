__author__ = 'christoph'

bFigureType = "PDF"

import numpy as np
import matplotlib as mpl

showPlot = True
savePlot = True    # save file as pdf?
name = "fig_flexibilityOfTimeStepOdd"

if bFigureType == "PGF":
    mpl.use('pgf')

pgf_with_custom_preamble = {
    "font.family": "serif", # use serif/main font for text elements
    "font.size": 24,
    "axes.labelsize": 22,
    "legend.fontsize": 24,
    "xtick.labelsize": 20,
    "ytick.labelsize": 20,
    "lines.linewidth": 3,
    "axes.linewidth": 1,
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

fig, ax = plt.subplots()

ax.plot([0,0.45,0.55,1], [0,1,1,0], color='forestgreen', linestyle='-')

ax.set_ylabel(r'Flexibility$_{t}^{rel}$', labelpad=20)
ax.set_xlabel(r'ML\_Ratio$_t^{ON}$', labelpad=20)

ax.set_xticks([0.45, 0.55])
ax.set_xticklabels(["", ""])
ax.set_xticks([0.5, 1], minor=True)
ax.set_xticklabels([r'$0.5 - \frac {1}{2 S}$ \quad $0.5 + \frac {1}{2 S}$', r'$1$'], minor=True)
for tick in ax.get_xaxis().get_minor_ticks():
    tick.set_pad(10)
    tick.label1 = tick._get_text1()
for line in ax.xaxis.get_minorticklines():
    line.set_visible(False)


ax.set_yticks([0, 1])

ax.set_ylim(0, 1.1)

ax.xaxis.grid()
ax.yaxis.grid()

fig.subplots_adjust(top=0.9, bottom=0.2, left=0.15, right=0.85)

fig.patch.set_facecolor('white')

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/" + name
    fig.savefig(fig_name + ".pdf")
