__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt


interval = 86400
stepsize = 900


resultfile = '../results/LPOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-10_10-36-33/results_log.txt'
resultfile_bi = '../results/LPOPT_SD365_RES25_bivalent_step900_dynCOP_T2015-03-10_20-05-37/results_log.txt'
resultfile_uncoord = '../results/LocalBest_SD365_RES25_mono_step900_dynCOP_T2015-03-13_11-04-25/results_log.txt'
resultfile_uncoord_bi = '../results/LocalBest_SD365_RES25_bivalent_step900_dynCOP_T2015-03-13_19-53-40/results_log.txt'
resultfile_multi = '../results/RMOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-11_00-53-46/results_log.txt'
resultfile_multi_bi = '../results/RMOPT_SD365_RES25_bivalent_step900_dynCOP_T2015-03-14_13-58-52/results_log.txt'

extractor = ResultExtractor(resultfile, interval, stepsize, 1, 365)
extractor_bi = ResultExtractor(resultfile_bi, interval, stepsize, 1, 365)
ex_un = ResultExtractor(resultfile_uncoord, interval, stepsize, 1, 365)
ex_un_bi = ResultExtractor(resultfile_uncoord_bi, interval, stepsize, 1, 365)
ex_multi = ResultExtractor(resultfile_multi, interval, stepsize, 1,365)
ex_multi_bi = ResultExtractor(resultfile_multi_bi, interval, stepsize, 1, 365)

extractor.extractResults()
extractor_bi.extractResults()
ex_un.extractResults()
ex_un_bi.extractResults()
ex_multi.extractResults()
ex_multi_bi.extractResults()

LDC_remainder = extractor.getLoadDuration_Remainder()
LDC_fluctuation = extractor.getLoadDuration_Fluct()
LDC_remainder_bi = extractor_bi.getLoadDuration_Remainder()
LDC_fluctuation_bi = extractor_bi.getLoadDuration_Fluct()
LDC_remainder_un = ex_un.getLoadDuration_Remainder()
LDC_remainder_un_bi = ex_un_bi.getLoadDuration_Remainder()
LDC_remainder_multi = ex_multi.getLoadDuration_Remainder()
LDC_remainder_multi_bi = ex_multi_bi.getLoadDuration_Remainder()

print "max fluct: {0} W".format(max(LDC_fluctuation))
print "min fluct: {0} W\n".format(min(LDC_fluctuation))
print "max tree mono: {0} W".format(max(LDC_remainder))
print "min tree mono: {0} W\n".format(min(LDC_remainder))
print "max tree bi: {0} W".format(max(LDC_remainder_bi))
print "min tree bi: {0} W\n".format(min(LDC_remainder_bi))
print "max uncoord mono: {0} W".format(max(LDC_remainder_un))
print "min uncoord mono: {0} W\n".format(min(LDC_remainder_un))
print "max uncoord bi: {0} W".format(max(LDC_remainder_un_bi))
print "min uncoord bi: {0} W\n".format(min(LDC_remainder_un_bi))
print "max multi mono: {0} W".format(max(LDC_remainder_multi))
print "min multi mono: {0} W\n".format(min(LDC_remainder_multi))
print "max multi bi: {0} W".format(max(LDC_remainder_multi_bi))
print "min multi bi: {0} W\n".format(min(LDC_remainder_multi_bi))

TimeAxis = [i*stepsize for i in range(len(LDC_remainder))]
zeros = [0 for n in range(len(TimeAxis))]

#plot

#plot
#latex settings for plot
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

fig = plt.figure()
#plt.plot(TimeAxis, zeros, 'k')
plt.plot(TimeAxis, LDC_fluctuation, 'k', label=r'\small{fluctuation}', linewidth=1)
plt.plot(TimeAxis, LDC_remainder_un, 'g', label=r'\small{uncoordinated PyCity 1}', linewidth=1)
plt.plot(TimeAxis, LDC_remainder_un_bi, 'g--', label=r'\small{uncoordinated PyCity 2}', linewidth=1)
plt.plot(TimeAxis, LDC_remainder, 'r', label=r'\small{tree-based PyCity 1}', linewidth=1)
plt.plot(TimeAxis, LDC_remainder_bi, 'r--', label=r'\small{tree-based PyCity 2}', linewidth=1)
plt.plot(TimeAxis, LDC_remainder_multi, 'b', label=r'\small{multicast-based PyCity 1}', linewidth=1)
plt.plot(TimeAxis, LDC_remainder_multi_bi, 'b--', label=r'\small{multicast-based PyCity 2}', linewidth=1)

plt.xlabel(r'\small{time [s]}')
plt.ylabel(r'\small{power [W]}')
plt.xlim([min(TimeAxis)-1000000,max(TimeAxis)+1000000])
plt.ylim([min(LDC_remainder_un)-5000, max(LDC_remainder_un_bi)+5000])

plt.grid(True)
plt.subplots_adjust(hspace=0.5, wspace=0.5, left=0.1, right=0.97, bottom=0.1, top=0.95)
plt.legend(loc='upper right', ncol=1)
#plt.text(150, 0.25, 'average RPTV: {0:.4f}'.format(avg_RPTV), fontsize=10)
fig.set_size_inches(8.5, 6.2)
plt.savefig("fig_LDC_PyCity_25RES", dpi=500)
