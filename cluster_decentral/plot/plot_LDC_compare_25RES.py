__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt


interval = 86400
stepsize = 900


resultfile_tree = '../results/LPOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-10_10-36-33/results_log.txt'
resultfile_tree_bi = '../results/LPOPT_SD365_RES25_bivalent_step900_dynCOP_T2015-03-10_20-05-37/results_log.txt'
resultfile_multi = '../results/RMOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-11_00-53-46/results_log.txt'
resultfile_multi_bi = '../results/RMOPT_SD365_RES25_bivalent_step900_dynCOP_T2015-03-14_13-58-52/results_log.txt'

ex_tree = ResultExtractor(resultfile_tree, interval, stepsize, 1, 365)
ex_tree_bi = ResultExtractor(resultfile_tree_bi, interval, stepsize, 1, 365)
ex_multi = ResultExtractor(resultfile_multi, interval, stepsize, 1, 365)
ex_multi_bi = ResultExtractor(resultfile_multi_bi, interval, stepsize, 1, 365)
ex_tree.extractResults()
ex_tree_bi.extractResults()
ex_multi.extractResults()
ex_multi_bi.extractResults()

LDC_remainder_tree = ex_tree.getLoadDuration_Remainder()
#LDC_fluctuation = ex_tree.getLoadDuration_Fluct()
LDC_remainder_tree_bi = ex_tree_bi.getLoadDuration_Remainder()
#LDC_fluctuation_bi = ex_tree_bi.getLoadDuration_Fluct()
LDC_remainder_multi = ex_multi.getLoadDuration_Remainder()
LDC_remainder_multi_bi = ex_multi_bi.getLoadDuration_Remainder()

TimeAxis = [i*stepsize for i in range(len(LDC_remainder_tree))]
zeros = [0 for n in range(len(TimeAxis))]

#plot

#plot
#latex settings for plot
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

fig = plt.figure()
#plt.plot(TimeAxis, zeros, 'k')
#plt.plot(TimeAxis, LDC_fluctuation, 'k', label=r'\small{fluctuation}')
plt.plot(TimeAxis, LDC_remainder_multi, 'g', label=r'\small{multicast-based PyCity 1}')
plt.plot(TimeAxis, LDC_remainder_multi_bi, 'b', label=r'\small{multicast-based PyCity 2}')
plt.plot(TimeAxis, LDC_remainder_tree, 'r--', label=r'\small{tree-based PyCity 1}')
plt.plot(TimeAxis, LDC_remainder_tree_bi, 'y--', label=r'\small{ tree-based PyCity 2}')


plt.xlabel(r'\small{time [s]}')
plt.ylabel(r'\small{power [W]}')
plt.xlim([min(TimeAxis)-1000000,max(TimeAxis)+1000000])
plt.ylim([min(LDC_remainder_multi)-5000, max(LDC_remainder_tree_bi)+5000])

plt.grid(True)
plt.subplots_adjust(hspace=0.5, wspace=0.5, left=0.13, right=0.99, bottom=0.15, top=0.95)
plt.legend(loc='upper right', ncol=1)
#plt.text(150, 0.25, 'average RPTV: {0:.4f}'.format(avg_RPTV), fontsize=10)
fig.set_size_inches(6.2, 3.0)
plt.savefig("fig_compare_LDC_25RES", dpi=300)
