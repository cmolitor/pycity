__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------


savePlot = True    # save file as pdf?
showPlot = True    # display plot?
#noBes = 480         # no of BES (manually update this for correct numbers of BESs per cluster)

markerM = 'b-'      # marker style for results of random clustering
markerS = 'g-'      # marker style for results of balanced clustering
markerR = 'r-'      # marker style for results of balanced clustering
ms_M = 2            # marker size for results of random clustering
ms_S = 2            # marker size for results of balanced clustering
ms_R = 2            # marker size for results of balanced clustering

width = 10.0         # in inches
height = 6.0        # in inches
noOfYTicks = 4      # number of ticks on y axis of each subplot

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


# save data
# ---------

ap1 = [2.1, 9.7, 19.1, 24.3, 21.9, 9.3, 5.3, 8.3]
ap2 = [6.5, 20.5, 28.6, 22.2, 12.2, 5.8, 2.7, 1.7]
ap3 = [8.1, 28.9, 33.0, 18.6, 7.5, 2.5, 0.8, 0.5]
ap7 = [9.5, 36.8, 35.0, 13.7, 3.5, 1.0, 0.3, 0.3]
ap13 = [9.8, 40.4, 33.9, 12.1, 2.8, 0.6, 0.1, 0.2]


ind = np.arange(8)
width = 0.15

# create subplots
#fig, ax = plt.subplots(dpi=200, figsize=(width, height) sharex=True, sharey=False)
fig, ax = plt.subplots()

rectsAp1 = ax.bar(ind, ap1, width=width, color='yellowgreen')
rectsAp2 = ax.bar(ind+width, ap2, width, color='darkorange')
rectsAp3 = ax.bar(ind+2*width, ap3, width, color='gold')
rectsAp7 = ax.bar(ind+3*width, ap7, width, color='lightskyblue')
rectsAp13 = ax.bar(ind+4*width, ap13, width, color='lightcoral')

# labeling etc
# ------------

ax.set_ylabel('Percentage of Buildings in %', labelpad=20)
ax.set_xlabel(r'Thermal Demand in $\frac{kWh}{m^2 a}$', labelpad=20)

ax.set_xticks(ind+width)
ax.set_xticklabels( ('40-80', '80-120', '120-160', '160-200', '200-240', '240-280', '280-320', '320-560'), rotation=45 )
ax.set_xlim([0-width, max(ind)+1])

test = fig.legend((rectsAp1, rectsAp2, rectsAp3, rectsAp7, rectsAp13), ('1 apt.', '2 apt.', '3-6 apt.', '7-12 apt.', '>12 apt.'), 'upper center', ncol=5)

fig.patch.set_facecolor('white')
fig.subplots_adjust(top=0.85, bottom=0.22, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/fig_Statistics_ThermalDemand"
    fig.savefig(fig_name + ".pdf")
