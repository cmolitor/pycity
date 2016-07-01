__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt

interval = 86400
stepsize = 900


#multicast, RSC3, monovalent, 0% RES
path_coord = '../results/RMOPT_SD365_RES0_mono_step900_dynCOP_T2015-03-08_12-20-19/results_log.txt'
#multicast, RSC3, monovalent, 50% RES
#path_coord = '../results/RMOPT_SD365_RES50_mono_step900_dynCOP_T2015-03-08_20-05-49/results_log.txt'
#multicast, RSC3, monovalent, 100% RES
path_coord = '../results/RMOPT_SD365_RES100_mono_step900_dynCOP_T2015-03-09_03-31-42/results_log.txt'

#uncoord, RSC3, monovalent, 0% RES
path_uncoord = '../results/LocalBest_SD365_RES0_mono_step900_dynCOP_T2015-03-09_10-49-12/results_log.txt'
#uncoord, RSC3, monovalent, 50% RES
#path_uncoord = '../results/LocalBest_SD365_RES50_mono_step900_dynCOP_T2015-03-09_15-17-55/results_log.txt'
#uncoord, RSC3, monovalent, 100% RES
path_uncoord = '../results/LocalBest_SD365_RES100_mono_step900_dynCOP_T2015-03-09_19-40-34/results_log.txt'

extractor_coord = ResultExtractor(path_coord, interval, stepsize, 1, 365)
extractor_uncoord = ResultExtractor(path_uncoord, interval, stepsize, 1, 365)
extractor_coord.extractResults()
extractor_uncoord.extractResults()

coord_remainders = extractor_coord.getRemainder()
uncoord_remainders = extractor_uncoord.getRemainder()

diff_remainders = []

for k in range(len(coord_remainders)):
    new_diff = [0 for x in range(len(coord_remainders[k]))]


    for t in range(len(coord_remainders[k])):
        new_diff[t] = uncoord_remainders[k][t] - coord_remainders[k][t]

    diff_remainders.append(new_diff)


# plot
# plot


curve=[]
for i in range(365):
    curve.extend(diff_remainders[i])


# calc sum up curve
sum_curve = []
sum_val = 0
for t in range(len(curve)):
    sum_val += curve[t]
    sum_curve.append(sum_val)

sorted_sum_curve_view = reversed(sorted(sum_curve))



sorted_sum_curve = []
for x in sorted_sum_curve_view:
    sorted_sum_curve.append(x)

Axis = [x*stepsize for x in range(len(curve))]

#latex settings for plot
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

fig = plt.figure()

plt.plot(Axis, curve, 'b')
plt.plot(Axis, sum_curve, 'r')
#plt.plot(Axis, sorted_sum_curve, 'g')
#plt.plot(dayAxis, curves[1], 'b')


plt.xlabel(r'\small{time [s]}')
plt.ylabel(r'\small{energy [Ws]}')
#plt.title('{0}: \n Number of Schedules'.format(self.resultfile_tree))

plt.grid(True)
plt.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.9)
plt.xlim([0, len(curve)*stepsize])
#plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
#           ncol=3, mode='expand',borderaxespad=0.)


fig.set_size_inches(6.2, 4.5)
#plt.legend(loc='lower right', ncol=1)
plt.savefig("fig_remainderdiff", dpi=300)
plt.show()