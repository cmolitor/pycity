__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA
from mpl_toolkits.axes_grid1 import host_subplot
import numpy as np


interval = 86400
stepsize = 900

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

# get plot data
multi_avgmsg_0RES = ex_multi_0RES.getAvgMessages()
multi_avgmsg_25RES = ex_multi_25RES.getAvgMessages()
multi_avgmsg_50RES = ex_multi_50RES.getAvgMessages()
multi_avgmsg_75RES = ex_multi_75RES.getAvgMessages()
multi_avgmsg_100RES = ex_multi_100RES.getAvgMessages()

tree_avgmsg_0RES = ex_tree_0RES.getAvgMessages()
tree_avgmsg_25RES = ex_tree_25RES.getAvgMessages()
tree_avgmsg_50RES = ex_tree_50RES.getAvgMessages()
tree_avgmsg_75RES = ex_tree_75RES.getAvgMessages()
tree_avgmsg_100RES = ex_tree_100RES.getAvgMessages()

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

#curves
tree_msg_curve = [tree_avgmsg_0RES, tree_avgmsg_25RES, tree_avgmsg_50RES, tree_avgmsg_75RES, tree_avgmsg_100RES]
multi_msg_curve = [multi_avgmsg_0RES, multi_avgmsg_25RES, multi_avgmsg_50RES, multi_avgmsg_75RES, multi_avgmsg_100RES]

tree_RPTV_curve = [tree_avgRPTV_0RES, tree_avgRPTV_25RES, tree_avgRPTV_50RES, tree_avgRPTV_75RES, tree_avgRPTV_100RES]
multi_RPTV_curve = [multi_avgRPTV_0RES, multi_avgRPTV_25RES, multi_avgRPTV_50RES, multi_avgRPTV_75RES, multi_avgRPTV_100RES]

print min(tree_msg_curve)
print max(tree_msg_curve)
print min(multi_msg_curve)
print max(multi_msg_curve)

#plot

#latex settings for plot
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

# x-Axis
#dayAxis = [r'\small{0 \% RES}', r'\small{25 \% RES}', r'\small{50 \% RES}', r'\small{75 \% RES}', r'\small{100 \% RES}']
RESAsix = np.array([0, 25, 50, 75, 100])

fig = plt.figure()
bar_width = 7
opacity = 1


#ax1.bar(StartersAxis-0.5*bar_width, msg_curve,  bar_width, color='r',alpha=opacity)
#ax1 = host_subplot(121, axes_class=AA.Axes)
ax1 = fig.add_subplot(121, title=r'\small{tree-based coordination}')
#ax1.plot(RESAsix, tree_msg_curve, 'ro', label=r'\small{messages tree}')
#ax1.plot(RESAsix, tree_msg_curve, 'r', label=r'\small{messages tree}')
ax1.bar(RESAsix-0.5*bar_width, tree_msg_curve, bar_width, color='r', alpha=opacity)
#ax1.plot(RESAsix, multi_msg_curve, 'bo', label=r'\small{messages multicast}')
#ax1.plot(RESAsix, multi_msg_curve, 'b', label=r'\small{messages multicast}')
#ax1.plot(dayAxis, multicast_msg_avg_curve, 'r--')
ax1.set_xlabel(r'\small{RES [\%]}')
ax1.set_ylabel(r'\small{average number of messages}')
#for tl in ax1.get_yticklabels():
#     tl.set_color('r')

ax2 = fig.add_subplot(122, title=r'\small{multicast-based coordination}')
#ax2.plot(RESAsix, multi_msg_curve, 'ro', label=r'\small{messages multicast}')
#ax2.plot(RESAsix, multi_msg_curve, 'r', label=r'\small{messages multicast}')
ax2.bar(RESAsix-0.5*bar_width, multi_msg_curve, bar_width, color='r', alpha=opacity)
ax2.set_xlabel(r'\small{RES [\%]}')
ax2.set_ylabel(r'\small{average number of messages}')
#ax11 = ax1.twinx()
#ax11.plot(RESAsix, tree_RPTV_curve, 'bo', label=r'\small{RPTV tree}')
#ax11.plot(RESAsix, tree_RPTV_curve, 'b', label=r'\small{RPTV tree}')
#ax11.plot(RESAsix, multi_RPTV_curve, 'bs', label=r'\small{RPTV multicast}')
#ax11.plot(RESAsix, multi_RPTV_curve, 'b--', label=r'\small{RPTV multicast}')
#ax11.plot(dayAxis, multicast_RPTV_avg_curve, 'b--')
#ax11.set_ylabel(r'\small{average RPTV}', color='b')
#for tl in ax11.get_yticklabels():
#    tl.set_color('b')

# turn on grid
ax1.grid(True)
ax2.grid(True)
#ax11.grid(True)
#plt.xlim([1,365])
ax1.set_xticks(np.arange(min(RESAsix), max(RESAsix)+1, 25))
ax2.set_xticks(np.arange(min(RESAsix), max(RESAsix)+1, 25))

#ax2.grid(True)
plt.subplots_adjust(hspace=0.5, wspace=0.4, left=0.1, right=0.99, bottom=0.15, top=0.9)

fig.set_size_inches(6.2, 3.0)

#plt.legend(loc='lower right', ncol=1)
plt.savefig("fig_msg_RES", dpi=300)
#plt.show()
