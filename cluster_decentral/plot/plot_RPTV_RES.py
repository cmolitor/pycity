__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA
from mpl_toolkits.axes_grid1 import host_subplot
import numpy as np


interval = 86400
stepsize = 900

slides = 1 # set to 0 if figures are for thesis, set to 1 if figures are for slides (changes font type and file name)

#extract results
resultfile_multicast_0RES = '../results/RMOPT_SD365_RES0_mono_step900_dynCOP_T2015-03-08_12-20-19/results_log.txt'
resultfile_multicast_25RES = '../results/RMOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-11_00-53-46/results_log.txt'
resultfile_multicast_50RES = '../results/RMOPT_SD365_RES50_mono_step900_dynCOP_T2015-03-08_20-05-49/results_log.txt'
resultfile_multicast_75RES = '../results/RMOPT_SD365_RES75_mono_step900_dynCOP_T2015-03-11_08-36-33/results_log.txt'
resultfile_multicast_100RES = '../results/RMOPT_SD365_RES100_mono_step900_dynCOP_T2015-03-09_03-31-42/results_log.txt'

ex_multi_0RES = ResultExtractor(resultfile_multicast_0RES, interval, stepsize, 1, 365)
ex_multi_25RES = ResultExtractor(resultfile_multicast_25RES, interval, stepsize, 1, 365)
ex_multi_50RES = ResultExtractor(resultfile_multicast_50RES, interval, stepsize, 1, 365)
ex_multi_75RES = ResultExtractor(resultfile_multicast_75RES, interval, stepsize, 1, 365)
ex_multi_100RES = ResultExtractor(resultfile_multicast_100RES, interval, stepsize, 1, 365)

ex_multi_0RES.extractResults()
ex_multi_25RES.extractResults()
ex_multi_50RES.extractResults()
ex_multi_75RES.extractResults()
ex_multi_100RES.extractResults()

resultfile_tree_0RES = '../results/LPOPT_SD365_RES0_mono_step900_dynCOP_T2015-03-07_22-07-21/results_log.txt'
resultfile_tree_25RES = '../results/LPOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-10_10-36-33/results_log.txt'
resultfile_tree_50RES = '../results/LPOPT_SD365_RES50_mono_step900_dynCOP_T2015-03-08_02-54-05/results_log.txt'
resultfile_tree_75RES = '../results/LPOPT_SD365_RES75_mono_step900_dynCOP_T2015-03-10_15-24-32/results_log.txt'
resultfile_tree_100RES = '../results/LPOPT_SD365_RES100_mono_step900_dynCOP_T2015-03-08_07-37-20/results_log.txt'

ex_tree_0RES = ResultExtractor(resultfile_tree_0RES, interval, stepsize, 1, 365)
ex_tree_25RES = ResultExtractor(resultfile_tree_25RES, interval, stepsize, 1, 365)
ex_tree_50RES = ResultExtractor(resultfile_tree_50RES, interval, stepsize, 1, 365)
ex_tree_75RES = ResultExtractor(resultfile_tree_75RES, interval, stepsize, 1, 365)
ex_tree_100RES = ResultExtractor(resultfile_tree_100RES, interval, stepsize, 1, 365)

ex_tree_0RES.extractResults()
ex_tree_25RES.extractResults()
ex_tree_50RES.extractResults()
ex_tree_75RES.extractResults()
ex_tree_100RES.extractResults()

resultfile_uncoord_0RES = '../results/LocalBest_SD365_RES0_mono_step900_dynCOP_T2015-03-09_10-49-12/results_log.txt'
resultfile_uncoord_25RES = '../results/LocalBest_SD365_RES25_mono_step900_dynCOP_T2015-03-13_11-04-25/results_log.txt'
resultfile_uncoord_50RES = '../results/LocalBest_SD365_RES50_mono_step900_dynCOP_T2015-03-09_15-17-55/results_log.txt'
resultfile_uncoord_75RES = '../results/LocalBest_SD365_RES75_mono_step900_dynCOP_T2015-03-13_15-29-16/results_log.txt'
resultfile_uncoord_100RES = '../results/LocalBest_SD365_RES100_mono_step900_dynCOP_T2015-03-09_19-40-34/results_log.txt'

ex_uncoord_0RES = ResultExtractor(resultfile_uncoord_0RES, interval, stepsize, 1, 365)
ex_uncoord_25RES = ResultExtractor(resultfile_uncoord_25RES, interval, stepsize, 1, 365)
ex_uncoord_50RES = ResultExtractor(resultfile_uncoord_50RES, interval, stepsize, 1, 365)
ex_uncoord_75RES = ResultExtractor(resultfile_uncoord_75RES, interval, stepsize, 1, 365)
ex_uncoord_100RES = ResultExtractor(resultfile_uncoord_100RES, interval, stepsize, 1, 365)

ex_uncoord_0RES.extractResults()
ex_uncoord_25RES.extractResults()
ex_uncoord_50RES.extractResults()
ex_uncoord_75RES.extractResults()
ex_uncoord_100RES.extractResults()


# get plot data
multi_avgRPTV_0RES = ex_multi_0RES.getAvgRelPTV()
multi_avgRPTV_25RES = ex_multi_25RES.getAvgRelPTV()
multi_avgRPTV_50RES = ex_multi_50RES.getAvgRelPTV()
multi_avgRPTV_75RES = ex_multi_75RES.getAvgRelPTV()
multi_avgRPTV_100RES = ex_multi_100RES.getAvgRelPTV()

tree_avgRPTV_0RES = ex_tree_0RES.getAvgRelPTV()
tree_avgRPTV_25RES = ex_tree_25RES.getAvgRelPTV()
tree_avgRPTV_50RES = ex_tree_50RES.getAvgRelPTV()
tree_avgRPTV_75RES = ex_tree_75RES.getAvgRelPTV()
tree_avgRPTV_100RES = ex_tree_100RES.getAvgRelPTV()

uncoord_avgRPTV_0RES = ex_uncoord_0RES.getAvgRelPTV()
uncoord_avgRPTV_25RES = ex_uncoord_25RES.getAvgRelPTV()
uncoord_avgRPTV_50RES = ex_uncoord_50RES.getAvgRelPTV()
uncoord_avgRPTV_75RES = ex_uncoord_75RES.getAvgRelPTV()
uncoord_avgRPTV_100RES = ex_uncoord_100RES.getAvgRelPTV()

#curves
tree_RPTV_curve = [tree_avgRPTV_0RES, tree_avgRPTV_25RES, tree_avgRPTV_50RES, tree_avgRPTV_75RES, tree_avgRPTV_100RES]
multi_RPTV_curve = [multi_avgRPTV_0RES, multi_avgRPTV_25RES, multi_avgRPTV_50RES, multi_avgRPTV_75RES, multi_avgRPTV_100RES]
uncoord_RPTV_curve = [uncoord_avgRPTV_0RES, uncoord_avgRPTV_25RES, uncoord_avgRPTV_50RES, uncoord_avgRPTV_75RES, uncoord_avgRPTV_100RES]

#plot

#latex settings for plot
plt.rc('text', usetex=True)
if slides:
    plt.rc('font', family='sans-serif')
else:
    plt.rc('font', family='serif')

# x-Axis
#dayAxis = [r'\small{0 \% RES}', r'\small{25 \% RES}', r'\small{50 \% RES}', r'\small{75 \% RES}', r'\small{100 \% RES}']
RESAsix = [0, 25, 50, 75, 100]

fig = plt.figure()

ax1 = fig.add_subplot(211)
ax1.plot(RESAsix, uncoord_RPTV_curve, 'go')
l1, = ax1.plot(RESAsix, uncoord_RPTV_curve, 'g', label=r'\small{uncoordinated}')
ax1.set_ylabel(r'\small{average RPTV}')

plt.grid(True)

ax2 = fig.add_subplot(212)
ax2.plot(RESAsix, tree_RPTV_curve, 'ro')
l2, = ax2.plot(RESAsix, tree_RPTV_curve, 'r', label=r'\small{tree-based}')
ax2.plot(RESAsix, multi_RPTV_curve, 'bo')
l3, = ax2.plot(RESAsix, multi_RPTV_curve, 'b', label=r'\small{multicast-based}')

ax2.set_xlabel(r'\small{RES [\%]}')
ax2.set_ylabel(r'\small{average RPTV}')

# turn on grid
plt.grid(True)
#ax1.grid(True)
#ax2.gird(True)
ax1.set_xlim([min(RESAsix)-2, max(RESAsix)+2])
ax2.set_xlim([min(RESAsix)-2, max(RESAsix)+2])
ax1.set_ylim([min(uncoord_RPTV_curve)-0.02, max(uncoord_RPTV_curve)+0.02])
ax2.set_ylim([min(multi_RPTV_curve)-0.02, max(tree_RPTV_curve)+0.02])
ax1.set_xticks(np.arange(min(RESAsix), max(RESAsix)+1, 25))
ax2.set_xticks(np.arange(min(RESAsix), max(RESAsix)+1, 25))

plt.subplots_adjust(hspace=0.2, wspace=0.5, left=0.1, right=0.98, bottom=0.15, top=0.8)

fig.set_size_inches(6.2, 3.5)

#plt.legend(loc='upper left', ncol=1)
#ax1.legend(loc='upper center')
#ax2.legend(loc='upper center')
fig.legend([l1, l2, l3], [r'\small{uncoordinated}', r'\small{tree-based}', r'\small{multicast-based}'], loc='upper center', ncol=3)

if slides:
    plt.savefig("fig_RPTV_allRES_slides", dpi=300)
else:
    plt.savefig("fig_RPTV_allRES", dpi=300)
#plt.show()
