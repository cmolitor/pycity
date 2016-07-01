__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA
from mpl_toolkits.axes_grid1 import host_subplot
import  numpy as np

interval = 86400
stepsize = 900

file_1 = '../results/RMOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-11_00-53-46/results_log.txt'
file_2 = '../results/RMOPT_SD137_RES25_mono_step900_2Starters_T2015-03-19_11-40-59/results_log.txt'
file_4 = '../results/RMOPT_SD31_RES25_mono_step900_4Starters_T2015-03-19_19-43-52/results_log.txt'
file_8 = '../results/RMOPT_SD79_RES25_mono_step900_8Starters_T2015-03-19_11-28-39/results_log.txt'
file_16 = '../results/RMOPT_SD43_RES25_mono_step900_16Starters_T2015-03-19_11-26-59/results_log.txt'

ex_1 = ResultExtractor(file_1, interval, stepsize, 1, 31)
ex_2 = ResultExtractor(file_2, interval, stepsize, 1, 31)
ex_4 = ResultExtractor(file_4, interval, stepsize, 1, 31)
ex_8 = ResultExtractor(file_8, interval, stepsize, 1, 31)
ex_16 = ResultExtractor(file_16, interval, stepsize, 1, 31)

ex_1.extractResults()
ex_2.extractResults()
ex_4.extractResults()
ex_8.extractResults()
ex_16.extractResults()

msg1 = ex_1.getAvgMessages()
msg2 = ex_2.getAvgMessages()
msg4 = ex_4.getAvgMessages()
msg8 = ex_8.getAvgMessages()
msg16 = ex_16.getAvgMessages()

RPTV1 = ex_1.getAvgRelPTV()
RPTV2 = ex_2.getAvgRelPTV()
RPTV4 = ex_4.getAvgRelPTV()
RPTV8 = ex_8.getAvgRelPTV()
RPTV16 = ex_16.getAvgRelPTV()

msg_curve = [msg1, msg2, msg4, msg8, msg16]
RPTV_curve = [RPTV1, RPTV2, RPTV4, RPTV8, RPTV16]

print msg_curve
print RPTV_curve

StartersAxis = np.array([1,2,4,8,16])
StartersAxis_msg = [0.5, 1.5, 3.5, 7.5, 15.5]
StartersAxis_RPTV = [1.5, 2.5, 4.5, 8.5, 16.5]

#plot

#latex settings for plot
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

fig = plt.figure()
#ax1 = host_subplot(121, axes_class=AA.Axes)
bar_width = 0.5
opacity = 1

ax1 = fig.add_subplot(111)
ax1.bar(StartersAxis-0.5*bar_width, msg_curve,  bar_width, color='r',alpha=opacity)
#ax1.plot(StartersAxis, msg_curve, 'ro')
#ax1.plot(StartersAxis, msg_curve, 'r')
#ax1.bar(StartersAxis, msg_curve, bar_width, color='r', )
ax1.set_xlabel(r'\small{number of starting BES-Agents}')
ax1.set_ylabel(r'\small{average number of messages}', color='r')
#for tl in ax1.get_yticklabels():
#     tl.set_color('r')

ax11 = ax1.twinx()
ax11.plot(StartersAxis, RPTV_curve, 'bo')
ax11.plot(StartersAxis, RPTV_curve, 'b')
ax11.set_ylabel(r'\small{average RPTV}', color='b')
#for tl in ax11.get_yticklabels():
#    tl.set_color('b')

# turn on grid
ax1.grid(True)
ax11.grid(True)
#ax11.grid(True)
#plt.xlim([1,365])
ax1.set_xticks(StartersAxis)
#ax1.set_xscale('log', basex=2)
#ax11.set_xscale('log', basex=2)


#ax2.grid(True)
plt.subplots_adjust(hspace=0.5, wspace=0.5, left=0.15, right=0.9, bottom=0.17, top=0.9)

fig.set_size_inches(6.2, 2.5)

#plt.legend(loc='lower right', ncol=1)
plt.savefig("fig_multi_starters", dpi=300)