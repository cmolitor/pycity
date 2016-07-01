__author__ = 'Annika Wierichs'


__author__ = 'Annika Wierichs'

import os
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

# some parameters for plot
# ------------------------

savePlot = True    # save file as pdf?
showPlot = True    # display plot?

name = 'fig_nomPowerAlg'

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

# load results from given path
# ----------------------------

nomPowers = [13865, 10229, 5470, 5378,
             5102, 4640, 4521, 3384,
             3014, 2723, 2683, 2551,
             2522, 2421, 2406, 2194,
             2168, 1890, 1771, 1348]

ind = np.arange(4)
width = 0.5

powerAcc = np.zeros(4)
indizes = np.zeros(len(nomPowers))
for b in range(len(nomPowers)):
    clIndex = np.argmin(powerAcc)  # add to the cluster currently accumulating lowest Flex*NomPower value
    powerAcc[clIndex] += abs(nomPowers[b])
    indizes[b] = clIndex


r = [[0 for _ in range(10)] for c in range(len(powerAcc))]
for b in range(len(nomPowers)):
    i = np.argmin(r[int(indizes[b])])
    r[int(indizes[b])][i] = nomPowers[b]

r = np.swapaxes(r,0,1)

# create subplots
#fig, ax = plt.subplots(dpi=200, figsize=(width, height) sharex=True, sharey=False)
fig, ax = plt.subplots()

rects1 = ax.bar(ind, r[0], width, color=['#000019','#000033','#00004c','#000066'])
rects2 = ax.bar(ind, r[1], width, color=['#3232ff','#0000cc','#000099','#00007f'], bottom=r[0])
rects3 = ax.bar(ind, r[2], width, color=['#9999ff','#1919ff','#0000b2','#0000e5'], bottom=r[1]+r[0])
rects4 = ax.bar(ind, r[3], width, color=['#ccccff','#7f7fff','#4c4cff','#0000ff'], bottom=r[2]+r[1]+r[0])
rects5 = ax.bar(ind, r[4], width, color=['#000000','#eaeaff','#b2b2ff','#6666ff'], bottom=r[3]+r[2]+r[1]+r[0])
rects6 = ax.bar(ind, r[5], width, color=['#000000','#000000','#000000','#e5e5ff'], bottom=r[4]+r[3]+r[2]+r[1]+r[0])

# labeling etc
# ------------

ax.set_ylabel('Nominal Power in W', labelpad=20)
ax.set_xlabel('Cluster', labelpad=20)

ax.set_xticks(ind+width/2)
ax.set_xticklabels( ('1', '2', '3', '4') )
ax.set_xlim([0-width, max(ind)+1])

fig.patch.set_facecolor('white')
fig.subplots_adjust(top=0.85, bottom=0.125, left=0.15, right=0.85)

if showPlot:
    plt.show()

# save file
if savePlot:
    fig_name = os.path.dirname(__file__) + "/../../../cm116988_BA_Annika_Wierichs/01_LatexDocument/plots/" + name
    fig.savefig(fig_name + ".pdf")