__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt


interval = 86400
stepsize = 900


resultfile = '../results/RMOPT_SD365_RES75_mono_step900_dynCOP_T2015-03-11_08-36-33/results_log.txt'
resultfile_bi = '../results/RMOPT_SD365_RES75_bivalent_step900_dynCOP_T2015-03-15_19-20-17/results_log.txt'
resultfile_uncoord = '../results/LocalBest_SD365_RES75_mono_step900_dynCOP_T2015-03-13_15-29-16/results_log.txt'
resultfile_uncoord_bi = '../results/LocalBest_SD365_RES75_bivalent_step900_dynCOP_T2015-03-18_11-22-59/results_log.txt'
extractor = ResultExtractor(resultfile, interval, stepsize, 1, 365)
extractor_bi = ResultExtractor(resultfile_bi, interval, stepsize, 1, 365)
ex_un = ResultExtractor(resultfile_uncoord, interval, stepsize, 1, 365)
ex_un_bi = ResultExtractor(resultfile_uncoord_bi, interval, stepsize, 1, 365)
extractor.extractResults()
extractor_bi.extractResults()
ex_un.extractResults()
ex_un_bi.extractResults()

LDC_remainder = extractor.getLoadDuration_Remainder()
LDC_fluctuation = extractor.getLoadDuration_Fluct()
LDC_remainder_bi = extractor_bi.getLoadDuration_Remainder()
LDC_fluctuation_bi = extractor_bi.getLoadDuration_Fluct()
LDC_remainder_un = ex_un.getLoadDuration_Remainder()
LDC_remainder_un_bi = ex_un_bi.getLoadDuration_Remainder()

TimeAxis = [i*stepsize for i in range(len(LDC_remainder))]
zeros = [0 for n in range(len(TimeAxis))]

#plot

#plot
#latex settings for plot
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

fig = plt.figure()
#plt.plot(TimeAxis, zeros, 'k')
plt.plot(TimeAxis, LDC_fluctuation, 'k', label=r'\small{fluctuation}')
plt.plot(TimeAxis, LDC_remainder_un, 'g', label=r'\small{uncoord. PyCity 1}')
plt.plot(TimeAxis, LDC_remainder_un_bi, 'g--', label=r'\small{uncoord. PyCity 2}')
plt.plot(TimeAxis, LDC_remainder, 'b', label=r'\small{multicast-based PyCity 1}')
plt.plot(TimeAxis, LDC_remainder_bi, 'b--', label=r'\small{ multicast-based PyCity 2}')


plt.xlabel(r'\small{time [s]}')
plt.ylabel(r'\small{power [W]}')
plt.xlim([min(TimeAxis)-1000000,max(TimeAxis)+1000000])
plt.ylim([min(LDC_remainder_un)-5000, max(LDC_remainder_un_bi)+5000])

plt.grid(True)
plt.subplots_adjust(hspace=0.5, wspace=0.5, left=0.15, right=0.99, bottom=0.15, top=0.95)
plt.legend(loc='upper right', ncol=2)
#plt.text(150, 0.25, 'average RPTV: {0:.4f}'.format(avg_RPTV), fontsize=10)
fig.set_size_inches(6.2, 3.0)
plt.savefig("fig_multi_LDC_75RES", dpi=300)
