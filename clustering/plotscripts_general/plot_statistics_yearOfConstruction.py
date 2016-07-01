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

data = [13.4, 12.5, 11.0, 13.9, 14.2, 11.2, 13.3, 10.5]


ind = np.arange(8)
width = 0.5

# create subplots
#fig, ax = plt.subplots(dpi=200, figsize=(width, height) sharex=True, sharey=False)
fig, ax = plt.subplots()

rects = ax.bar(ind+width/2, data, width=width, color='gold')

# labeling etc
# ------------

ax.set_ylabel('Percentage of Buildings in %', labelpad=20)
ax.set_xlabel('Year of construction', labelpad=20)

ax.set_xticks(ind+width/2)
ax.set_xticklabels( ('< 1919', '1919 - 1949', '1950 - 1959', '1960 - 1969', '1970 - 1979', '1980 - 1989', '1990 - 1999', '> 2000'), rotation=45 )
ax.xaxis.set_tick_params(width=0, length=0)


fig.patch.set_facecolor('white')
fig.subplots_adjust(top=0.85, bottom=0.25, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/fig_Statistics_YearOfConstruction"
    fig.savefig(fig_name + ".pdf")

