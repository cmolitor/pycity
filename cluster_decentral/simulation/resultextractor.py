__author__ = 'Sonja Kolen'

import os
import fileinput
import re
import matplotlib.pyplot as plt
import numpy as np
from scipy import interpolate


class ResultExtractor():

    def __init__(self, result_file, interval, stepsize, startDay, endDay):
        """
        This class is used to extract simulation results
        :param result_file: path to result file
        :param interval: interval of simulation (e.g. 86400 sec for 24h)
        :param startDay: start day for result extraction
        :param endDay: end day for result extraction
        :return:
        """
        self.resultfile = result_file           #save path to result file as string
        #if not os.path.isfile(self.resultfile_tree):
        #    print 'ResultExtractor error: {0} does not exist. Abort.'.format(self.resultfile_tree)
        #    exit()
        self.startDay = startDay
        self.endDay = endDay
        self.interval = interval
        self.stepsize = stepsize

        # result variables
        self.fluctuation = []                   # saves fluctuation curve [Watt]
        self.remainder = []                     # saves remainder curve [Watt]
        self.load = []                          # saves load curve [Watt]
        self.maxmindiff_improvement = []        # saves improvement of maxmindiff per day [%]
        self.absremainder_improvement = []      # saves improvement of absolute remainder per day [%]
        self.runtime = []                       # saves runtime [sec]
        self.avg_schedules = []                 # saves average number of schedules per BES per interval
        self.min_schedules = []                 # saves minimal number of schedules per BES per interval
        self.max_schedules = []                 # saves maximal number of schedules per BES per interval
        self.msg_sent = []                      # saves number of sent messages per interval
        self.msg_rec = []                       # saves number of received messages per interval

        self.time = []                          # saves time axis for fluct and remainder (mescos only)

    def extractResults(self):
        """
        extract result between startDay and endDay
        :return:
        """
        print 'Data extraction running...'
        numeric_const_pattern = r'[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?'

        lines_fluct = 1
        lines_remainder = 1
        no_days = self.endDay - self.startDay
        day_counter = 0

        current_day = -1
        current_day_finished = 1
        fluct_curr_day_finished = lines_fluct
        remainder_curr_day_finished = lines_remainder

        for line in fileinput.input(self.resultfile):
            if not line.startswith('CLUSTER: Time for NEGOTIATION PHASE in day {0}'.format(self.startDay)) and current_day == -1:
                continue
            elif line.startswith('CLUSTER: Time for NEGOTIATION PHASE in day {0}'.format(self.startDay)) and current_day == -1:
                current_day = self.startDay
                current_day_finished = 0    # current day not finished
                #extract runtime
                numbers = re.findall(numeric_const_pattern, line)
                self.runtime.append(float(numbers[1])*60+float(numbers[2]))
                day_counter += 1

            elif current_day != -1 and current_day <= self.endDay and line.startswith('CLUSTER: Time for NEGOTIATION PHASE in day {0}'.format(current_day)): # if there are still days to be extracted
                #extract runtime
                current_day_finished = 0
                numbers = re.findall(numeric_const_pattern, line)
                self.runtime.append(float(numbers[1])*60+float(numbers[2]))
                day_counter += 1

            elif not current_day_finished and line.startswith('CLUSTER: fluctuation | '): #extract fluctuation curve for day
                fluct_curr_day_finished = 0
                numbers = re.findall(numeric_const_pattern, line)
                fluct_part = []
                for n in range(len(numbers)):
                    fluct_part.append(float(numbers[n]))
                self.fluctuation.append(fluct_part)
                fluct_curr_day_finished += 1

            elif fluct_curr_day_finished < lines_fluct:
                numbers = re.findall(numeric_const_pattern, line)
                for n in range(len(numbers)):
                    self.fluctuation[day_counter-1].append(float(numbers[n]))
                fluct_curr_day_finished += 1
                if fluct_curr_day_finished == lines_fluct and len(self.fluctuation[day_counter-1]) > 24:
                    raw_input('stop fluct day {0}'.format(current_day))

            elif not current_day_finished and line.startswith('CLUSTER: loadcurve | '): #extract load curve for day
                numbers = re.findall(numeric_const_pattern, line)
                load = []
                for n in range(len(numbers)):
                    load.append(float(numbers[n]))
                self.load.append(load)

            elif not current_day_finished and line.startswith('CLUSTER: remainder | '): #extract remainder curve for day
                remainder_curr_day_finished = 0
                numbers = re.findall(numeric_const_pattern, line)
                reamainder_part = []
                for n in range(len(numbers)):
                    reamainder_part.append(float(numbers[n]))
                self.remainder.append(reamainder_part)
                remainder_curr_day_finished += 1

            elif remainder_curr_day_finished < lines_remainder:
                numbers = re.findall(numeric_const_pattern, line)
                for n in range(len(numbers)):
                    self.remainder[day_counter-1].append(float(numbers[n]))
                remainder_curr_day_finished += 1
                if remainder_curr_day_finished == lines_remainder and len(self.remainder[day_counter-1]) > 24:
                    raw_input('stop remainder day {0}'.format(current_day))

            elif not current_day_finished and line.startswith('CLUSTER: max-min-diff improvement'): #extract max min diff improvement
                number = re.findall(numeric_const_pattern, line)
                self.maxmindiff_improvement.append(float(number[0]))

            elif not current_day_finished and line.startswith('CLUSTER: abs improvement '): #extract abs remainder improvement
                number = re.findall(numeric_const_pattern, line)
                self.absremainder_improvement.append(float(number[0]))
                # AFTER ABSREMAINDER THE DATA FOR ONE DAY IS FINISHED
                current_day += 1
                current_day_finished = 1

            elif not current_day_finished and line.startswith('CLUSTER: average schedules |'):
                number = re.findall(numeric_const_pattern, line)
                self.avg_schedules.append(float(number[0]))

            elif not current_day_finished and line.startswith('CLUSTER: min schedules |'):
                number = re.findall(numeric_const_pattern, line)
                self.min_schedules.append(float(number[0]))

            elif not current_day_finished and line.startswith('CLUSTER: max schedules |'):
                number = re.findall(numeric_const_pattern, line)
                self.max_schedules.append(float(number[0]))

            elif not current_day_finished and line.startswith('CLUSTER: sent messages | '):
                number = re.findall(numeric_const_pattern, line)
                self.msg_sent.append(float(number[0]))

            elif not current_day_finished and line.startswith('CLUSTER: received messages | '):
                number = re.findall(numeric_const_pattern, line)
                self.msg_rec.append(float(number[0]))


        #print self.runtime
        #print self.fluctuation
        #print self.remainder
        #print self.maxmindiff_improvement
        #print self.absremainder_improvement

        #print len(self.runtime)
        #print len(self.fluctuation)
        #print len(self.remainder)
        #print len(self.maxmindiff_improvement)
        #print len(self.absremainder_improvement)

        fileinput.close()
        print 'Extraction finished!'

        return

    def extractResults_fromCSV(self, fluctcsv, messagecsv):
        """
        extract results from csv file (for MESCOS evaluation)
        :return:
        """
        _dataFluctuation = np.genfromtxt(fluctcsv, skip_header=1, delimiter=",")
        _dataMessages = np.genfromtxt(messagecsv, skip_header=1, delimiter=",")
        time_fluct = _dataFluctuation[:,0]
        fluctuation = _dataFluctuation[:,1]
        remainder = _dataFluctuation[:,2]
        self.msg_sent = _dataMessages[:,1]
        self.msg_rec = _dataMessages[:,2]

        stepSize = _dataFluctuation[1,0] - _dataFluctuation[0,0] #sec
        stepsPerDay = 86400 / stepSize;

        numberOfDays=int(len(time_fluct) / stepsPerDay)
        for d in range(numberOfDays):
            start_index=d*stepsPerDay
            fluct_day = fluctuation[start_index:start_index+stepsPerDay-1]
            self.fluctuation.append(fluct_day)

            remainder_day = remainder[start_index:start_index+stepsPerDay-1]
            self.remainder.append(remainder_day)

            time_day = time_fluct[start_index:start_index+stepsPerDay-1]
            self.time.append(time_day)





    def plot_all_results(self):
        """
        plot all results
        :return:
        """
        print 'plotting all results...'

        all_remainder = []
        all_fluctuation = []
        all_load = []

        for d in range(len(self.remainder)):
            for t in range(len(self.remainder[d])):
                all_remainder.append(self.remainder[d][t])
                all_fluctuation.append(self.fluctuation[d][t])
                all_load.append(self.load[d][t])

        #calc average improvements
        average_maxmindiff = float(sum(self.maxmindiff_improvement) / len(self.maxmindiff_improvement))
        average_absremainder = float(sum(self.absremainder_improvement) / len(self.absremainder_improvement))
        #print average_absremainder
        #print average_maxmindiff

        xAxis = [x for x in range(len(all_remainder))]
        zeros = [0 for x in range(len(all_remainder))]
        index = np.arange(len(all_remainder))
        index2 = np.arange(start=(self.startDay*(self.interval/self.stepsize)-(self.interval/self.stepsize)), stop=(self.endDay*(self.interval/self.stepsize)), step=self.interval/self.stepsize)
        bar_width = 0.5
        opacity = 0.5
        error_config={'ecolor': '0.3'}

        plt.plot(xAxis, zeros, 'black')
        plt.bar(index, all_fluctuation, bar_width, alpha=opacity, color='r', label='Fluctuation', error_kw=error_config)
        plt.bar(index, all_remainder, bar_width, alpha=opacity, color='b', label='Remainder', error_kw=error_config)
        plt.plot(index, all_load, 'g', label='Load Curve')
        plt.xticks(index[0::self.interval/self.stepsize], index2)

        plt.xlabel('Time [h]')
        plt.ylabel('Energy [W]')

        plt.title('{2}: \nAll results - day {0} to {1}'.format(self.startDay, self.endDay, self.resultfile))

        plt.legend(loc='lower left', ncol=3)
        #plt.tight_layout()
        plt.figtext(0.3,0.3,'Average Compensation of {0:.2f} %'.format(average_absremainder, fontsize=12))
        plt.figtext(0.3,0.25,'Average Max-Min-Diff Improvement {0:.2f} %'.format(average_maxmindiff, fontsize=12))
        plt.grid()
        plt.show()

        return

    def plot_criteria(self):
        """
        plot max min diff, absolute remainder and runtime
        :return:
        """
        window = 21
        avg_max_min = sum(self.maxmindiff_improvement) / len(self.maxmindiff_improvement)
        avg_abs_remainder = sum(self.absremainder_improvement) / len(self.absremainder_improvement)

        index = [x for x in range(self.startDay, self.endDay+1)]
        fig, ax1 = plt.subplots()


        #avg_max_min_curve = [avg_max_min for i in range(len(self.absremainder_improvement))]
        #avg_abs_remainder_curve = [avg_abs_remainder for k in range(len(self.maxmindiff_improvement))]

        mvgavg_maxmin = self.movingavearage(self.maxmindiff_improvement, window)
        mvgavg_absrem = self.movingavearage(self.absremainder_improvement, window)



        #ax1.plot(index, self.absremainder_improvement, 'ro', label='abs. remainder imp')
        #ax1.plot(index, mvgavg_absrem, 'r')
        ax1.plot(index, self.maxmindiff_improvement, 'bo', label='max-min-diff imp')
        ax1.plot(index, mvgavg_maxmin, 'b')
        #ax2.plot(index, self.runtime, color='g', label='runtime')

        ax1.set_xlabel('Day')
        ax1.set_ylabel('Improvement [%]')
        #ax2.set_ylabel('Time [sec]', color='g')

        plt.title('{2}: \n PTV improvement - day {0} to {1}'.format(self.startDay, self.endDay, self.resultfile))

        plt.legend(loc='lower left', ncol=3)
        #plt.figtext(0.3,0.2,'min abs remainder imp: {0:.2f} % | max abs remainder imp: {1:.2f} % | avg abs remainder imp: {2:.2f} %'.format(min(self.absremainder_improvement), max(self.absremainder_improvement), avg_abs_remainder, fontsize=12))
        plt.figtext(0.3,0.15,'min PTV imp: {0:.2f} % | max PTV imp: {1:.2f} % | avg PTV imp: {2:.2f} %'.format(min(self.maxmindiff_improvement), max(self.maxmindiff_improvement),avg_max_min, fontsize=12))
        plt.grid()
        plt.show()

    def plot_PTVimprovement(self):
        """
        plot improvement of max min diff
        :return:
        """
        window = 21
        avg_max_min = sum(self.maxmindiff_improvement) / len(self.maxmindiff_improvement)
        index = [x for x in range(self.startDay, self.endDay+1)]

        mvgavg_maxmin = self.movingavearage(self.maxmindiff_improvement, window)

        plt.plot(index, self.maxmindiff_improvement, 'bo', label='PTV imp')
        plt.plot(index, mvgavg_maxmin, 'b')

        plt.xlabel('Day')
        plt.ylabel('Improvement [%]')
        #ax2.set_ylabel('Time [sec]', color='g')

        plt.title('{2}: \n Peak-to-Valley improvement - day {0} to {1}'.format(self.startDay, self.endDay, self.resultfile))

        plt.legend(loc='lower left', ncol=1)

        plt.figtext(0.3,0.15,'min PTV imp: {0:.2f} % | max PTV imp: {1:.2f} % | avg PTV imp: {2:.2f} %'.format(min(self.maxmindiff_improvement), max(self.maxmindiff_improvement),avg_max_min, fontsize=12))
        plt.grid()
        plt.show()


    def plot_min_maxmindiff(self):
        """
        plot remainder of day with minimal max min diff improvement
        :return:
        """

        min_max_min_diff = min(self.maxmindiff_improvement)
        for i in range(len(self.maxmindiff_improvement)):
            if min_max_min_diff == self.maxmindiff_improvement[i]:
                break

        plt.title('{1}: \n MIN maxmindiff improvement at day {0}: {2:.2f} %'.format(self.startDay+i, self.resultfile, min_max_min_diff))

        xAxis = [x for x in range(len(self.remainder[i]))]
        zeros = [0 for x in range(len(self.remainder[i]))]
        index = np.arange(len(self.remainder[i]))
        bar_width = 0.5
        opacity = 0.5
        error_config={'ecolor': '0.3'}

        plt.plot(xAxis, zeros, 'black')
        plt.bar(index, self.fluctuation[i], bar_width, alpha=opacity, color='r', label='Fluctuation', error_kw=error_config)
        plt.bar(index, self.remainder[i], bar_width, alpha=opacity, color='b', label='Remainder', error_kw=error_config)
        plt.plot(index, self.load[i], 'g', label='Load Curve')

        plt.xlabel('Time [h]')
        plt.ylabel('Energy [W]')


        plt.legend(loc='lower left', ncol=3)
        #plt.tight_layout()
        plt.figtext(0.3,0.3,'abs remainder imp {0:.2f} %'.format(self.absremainder_improvement[i], fontsize=12))
        plt.figtext(0.3,0.25,'max-min-diff imp {0:.2f} %'.format(self.maxmindiff_improvement[i], fontsize=12))
        plt.grid()
        plt.show()

    def plot_max_maxmindiff_new(self):
        max_max_min_diff = max(self.maxmindiff_improvement)
        for i in range(len(self.maxmindiff_improvement)):
            if max_max_min_diff == self.maxmindiff_improvement[i]:
                break

        xAxis = [x for x in range(len(self.remainder[i]))]
        zeros = [0 for x in range(len(self.remainder[i]))]
        index = np.arange(len(self.remainder[i]))
        bar_width = 0.5
        opacity = 0.5
        error_config={'ecolor': '0.3'}

        plt.rcParams.update({'font.size': 30})

        plt.plot(xAxis, zeros, 'black')

        plt.plot(xAxis, zeros, 'black')
        plt.bar(index, self.fluctuation[i], bar_width, alpha=opacity, color='b', label='Fluctuation', error_kw=error_config)
        plt.bar(index, self.remainder[i], bar_width, alpha=opacity, color='darkorange', label='Remainder', error_kw=error_config)
        #plt.plot(index, self.load[i], 'g', label='Load Curve')

        plt.xlabel('time intervals in 15 min steps')
        plt.ylabel('energy [Ws]')


        plt.legend(loc='upper left', ncol=2)
        plt.grid()
        plt.show()


    def plot_max_maxmindiff(self):
        """
        plot remainder of day with maximal max min diff improvement
        :return:
        """

        max_max_min_diff = max(self.maxmindiff_improvement)
        for i in range(len(self.maxmindiff_improvement)):
            if max_max_min_diff == self.maxmindiff_improvement[i]:
                break


        #print self.startDay+i
        #print self.remainder[i]

        xAxis = [x for x in range(len(self.remainder[i]))]
        zeros = [0 for x in range(len(self.remainder[i]))]
        index = np.arange(len(self.remainder[i]))
        bar_width = 0.5
        opacity = 0.5
        error_config={'ecolor': '0.3'}

        plt.plot(xAxis, zeros, 'black')
        plt.bar(index, self.fluctuation[i], bar_width, alpha=opacity, color='r', label='Fluctuation', error_kw=error_config)
        plt.bar(index, self.remainder[i], bar_width, alpha=opacity, color='b', label='Remainder', error_kw=error_config)
        plt.plot(index, self.load[i], 'g', label='Load Curve')

        plt.xlabel('Time [h]')
        plt.ylabel('Energy [W]')


        plt.legend(loc='lower left', ncol=3)
        #plt.tight_layout()
        plt.figtext(0.3,0.3,'abs remainder imp {0:.2f} %'.format(self.absremainder_improvement[i], fontsize=12))
        plt.figtext(0.3,0.25,'max-min-diff imp {0:.2f} %'.format(self.maxmindiff_improvement[i], fontsize=12))
        plt.grid()
        plt.show()

    def plot_min_absremainder(self):
        """
        plot remainder of day with minimal abs remainder
        :return:
        """

        min_absremainder = min(self.absremainder_improvement)
        for i in range(len(self.absremainder_improvement)):
            if min_absremainder == self.absremainder_improvement[i]:
                break

        plt.title('{1}: \n MIN absremainder improvement at day {0}: {2:.2f} %'.format(self.startDay+i, self.resultfile, min_absremainder))

        xAxis = [x for x in range(len(self.remainder[i]))]
        zeros = [0 for x in range(len(self.remainder[i]))]
        index = np.arange(len(self.remainder[i]))
        bar_width = 0.5
        opacity = 0.5
        error_config={'ecolor': '0.3'}

        plt.plot(xAxis, zeros, 'black')
        plt.bar(index, self.fluctuation[i], bar_width, alpha=opacity, color='r', label='Fluctuation', error_kw=error_config)
        plt.bar(index, self.remainder[i], bar_width, alpha=opacity, color='b', label='Remainder', error_kw=error_config)
        plt.plot(index, self.load[i], 'g', label='Load Curve')

        plt.xlabel('Time [h]')
        plt.ylabel('Energy [W]')


        plt.legend(loc='lower left', ncol=3)
        #plt.tight_layout()
        plt.figtext(0.3,0.3,'abs remainder imp {0:.2f} %'.format(self.absremainder_improvement[i], fontsize=12))
        plt.figtext(0.3,0.25,'max-min-diff imp {0:.2f} %'.format(self.maxmindiff_improvement[i], fontsize=12))
        plt.grid()
        plt.show()

    def plot_max_absremainder(self):
        """
        plot remainder of day with minimal abs remainder
        :return:
        """

        max_absremainder = max(self.absremainder_improvement)
        for i in range(len(self.absremainder_improvement)):
            if max_absremainder == self.absremainder_improvement[i]:
                break

        plt.title('{1}: \n MAX absremainder improvement at day {0}: {2:.2f} %'.format(self.startDay+i, self.resultfile, max_absremainder))

        xAxis = [x for x in range(len(self.remainder[i]))]
        zeros = [0 for x in range(len(self.remainder[i]))]
        index = np.arange(len(self.remainder[i]))
        bar_width = 0.5
        opacity = 0.5
        error_config={'ecolor': '0.3'}

        plt.plot(xAxis, zeros, 'black')
        plt.bar(index, self.fluctuation[i], bar_width, alpha=opacity, color='r', label='Fluctuation', error_kw=error_config)
        plt.bar(index, self.remainder[i], bar_width, alpha=opacity, color='b', label='Remainder', error_kw=error_config)
        plt.plot(index, self.load[i], 'g', label='Load Curve')

        plt.xlabel('Time [h]')
        plt.ylabel('Energy [W]')


        plt.legend(loc='lower left', ncol=3)
        #plt.tight_layout()
        plt.figtext(0.3,0.3,'abs remainder imp {0:.2f} %'.format(self.absremainder_improvement[i], fontsize=12))
        plt.figtext(0.3,0.25,'max-min-diff imp {0:.2f} %'.format(self.maxmindiff_improvement[i], fontsize=12))
        plt.grid()
        plt.show()

    def plot_max_remainderfluct(self):
        """
        plot the maximal fluctuation and remainder values for each day
        :return:
        """
        window = 21
        max_fluct = []
        max_remainder = []

        for d in range(len(self.remainder)):
            max_fluct.append(max(self.fluctuation[d]))
            max_remainder.append(max(self.remainder[d]))

        mvavg_fluct = self.movingavearage(max_fluct, window)
        mvavg_rem = self.movingavearage(max_remainder, window)

        index = [x for x in range(self.startDay, self.endDay+1)]
        fig, ax1 = plt.subplots()

        ax1.plot(index, max_fluct, 'ro', label='max fluct')
        ax1.plot(index, mvavg_fluct, 'r')
        ax1.plot(index, max_remainder, 'bo', label='max remainder')
        ax1.plot(index, mvavg_rem, 'b')

        ax1.set_xlabel('Day')
        ax1.set_ylabel('Energy [Watt]')
        plt.title('{2}: \m Maximal fluctuation and remainder - day {0} to {1}'.format(self.startDay, self.endDay, self.resultfile))
        plt.legend(loc='lower left', ncol=4)
        plt.grid()
        plt.show()

    def plot_min_remainderfluct(self):
        """
        plot the min fluctuation and remainder values for each day
        :return:
        """
        window = 21
        min_fluct = []
        min_remainder = []

        for d in range(len(self.remainder)):
            min_fluct.append(min(self.fluctuation[d]))
            min_remainder.append(min(self.remainder[d]))

        mvavg_fluct = self.movingavearage(min_fluct, window)
        mvavg_rem = self.movingavearage(min_remainder, window)

        index = [x for x in range(self.startDay, self.endDay+1)]#]np.arange(len(self.absremainder_improvement))
        fig, ax1 = plt.subplots()

        ax1.plot(index, min_fluct, 'ro', label='min fluct')
        ax1.plot(index, mvavg_fluct, 'r')
        ax1.plot(index, min_remainder, 'bo', label='min remainder')
        ax1.plot(index, mvavg_rem, 'b')

        ax1.set_xlabel('Day')
        ax1.set_ylabel('Energy [Watt]')
        plt.title('{2}: \n Minimal fluctuation and remainder - day {0} to {1}'.format(self.startDay, self.endDay, self.resultfile))
        plt.legend(loc='lower left', ncol=4)
        plt.grid()
        plt.show()

    def plot_scheduledata(self):
        """
        plot average number of schedules
        :return:
        """
        window = 21
        index = [x for x in range(self.startDay, self.endDay+1)]
        fig, ax1 = plt.subplots()

        avg_movingavg = self.movingavearage(self.avg_schedules, window)
        #print len(avg_movingavg)
        #print avg_movingavg
        min_movingavg = self.movingavearage(self.min_schedules, window)
        max_movingavg = self.movingavearage(self.max_schedules, window)

        ax1.plot(index, self.avg_schedules, 'go', label='average num schedules')
        ax1.plot(index, avg_movingavg, 'g')
        ax1.plot(index, self.min_schedules, 'bo', label='min num schedules')
        ax1.plot(index, min_movingavg, 'b')
        ax1.plot(index, self.max_schedules, 'ro', label='max num schedules')
        ax1.plot(index, max_movingavg, 'r')
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Number of schedules')
        plt.title('{0}: \n Number of Schedules'.format(self.resultfile))
        plt.legend(loc='lower left', ncol=3)
        plt.grid()
        plt.show()


        return

    def plot_messages_sent_runtime(self):
        """
        plot number of sent messages and runtime in same plot
        :return:
        """
        window = 21
        index = [x for x in range(self.startDay, self.endDay+1)]
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        mvavg_runtime = self.movingavearage(self.runtime, window)
        mvavg_messages = self.movingavearage(self.msg_sent, window)

        line1 = ax1.plot(index, self.msg_sent, 'bo', label='sent messages')
        ax1.plot(index, mvavg_messages, 'b')
        line2 = ax2.plot(index, self.runtime, 'ro', label='runtime')
        ax2.plot(index, mvavg_runtime, 'r')
        #ax1.plot(index, self.msg_rec, 'r', label='received messages')
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Number of messages')
        ax2.set_ylabel('Time [sec]')
        plt.title('{0}: \n Number of sent messages and runtime'.format(self.resultfile))

        ax = line1+line2
        labs = [k.get_label() for k in ax]

        plt.legend(ax, labs, loc='lower left', ncol=3)
        plt.grid()
        plt.show()

    def plot_messages(self):
        """
        plot number of sent messages over time
        :return:
        """
        window = 21
        index = [x for x in range(self.startDay, self.endDay+1)]
        ax1 = plt.subplot()

        mvavg_messages = self.movingavearage(self.msg_sent, window)

        ax1.plot(index, self.msg_sent, 'bo', label='number of messages')
        ax1.plot(index, mvavg_messages, 'b', label='mvg average (w={0})'.format(window))
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Number of messages')
        plt.title('{0}: \n Number of sent messages'.format(self.resultfile))

        plt.legend(loc='lower left', ncol=2)
        plt.grid()
        plt.show()


    def movingavearage(self, values, window):
        """
        calculate moving avearge of values with window
        :param values: values that moving average shall be calculated for
        :param window: window size
        :return: moving average curve corresponding to values
        """
        if not window % 2:
            print 'Moving Avgerage error: window needs to be odd'
            return


        values_length = len(values)
        add_beginning = [values[0] for i in range((window-1)/2)]
        add_end = [values[-1] for k in range((window-1)/2)]

        new_values = add_beginning + values + add_end
        #print len(new_values)

        weights = np.repeat(1.0, window)/window
        mvavg = np.convolve(new_values, weights, 'valid')
        len_avg = len(mvavg)
        diff_length = len_avg - values_length
        #mvavg = mvavg[diff_length/2 + len(add_beginning)-1:len_avg-diff_length/2-len(add_end)-1]

        return mvavg

    def csvplot_result(self):
        """
        plot fluctuation and remainder from start day to end day
        :return:
        """

        fluct_curve = []
        remainder_curve = []
        time_axis = []
        if(self.endDay - self.startDay) == 0: #only one day
            fluct_curve = self.fluctuation[self.startDay-1]
            remainder_curve = self.remainder[self.startDay-1]
            time_axis = self.time[self.startDay-1]
        else:

            for d in range(self.endDay-self.startDay):
                fluct_curve.extend(self.fluctuation[d+self.startDay])
                remainder_curve.extend(self.remainder[d+self.startDay])
                time_axis.extend(self.time[d+self.startDay])

        bar_width = self.stepsize*0.6
        opacity = 0.5
        error_config={'ecolor': '0.3'}
        plt.title('Energy fluctuation and remainder from day {0} to {1}'.format(self.startDay, self.endDay))

       # plt.plot(time_axis, zeros, 'black')
        plt.bar(time_axis, fluct_curve, bar_width, alpha=opacity, color='r', label='Fluctuation', error_kw=error_config)
        plt.bar(time_axis, remainder_curve, bar_width, alpha=opacity, color='b', label='Remainder', error_kw=error_config)
        #plt.plot(time_axis, self.load[i], 'g', label='Load Curve')

        plt.xlabel('Time [sec]')
        plt.ylabel('Energy [Ws]')


        plt.legend(loc='lower left', ncol=2)
        #plt.tight_layout()
        plt.grid()
        plt.show()

    def plot_relativePowerAverage(self):
        """
        plot relative power average
        :return:
        """
        fluct_curve = []
        remainder_curve = []
        #time_axis = []
        #calc averages
        fluct_avg = []
        rem_avg = []

        for d in range(self.endDay-self.startDay):

            fluct_avg.append(0)
            rem_avg.append(0)
            for t in range(len(self.fluctuation[d+self.startDay-1])):
                fluct_avg[d] += self.fluctuation[d+self.startDay-1][t]
                rem_avg[d] += self.remainder[d+self.startDay-1][t]

            fluct_avg[d] /= len(self.fluctuation[d+self.startDay-1])
            rem_avg[d] /= len(self.remainder[d+self.startDay-1])

        RPA = []
        for t in range(len(fluct_avg)):
            RPA.append(rem_avg[t]/fluct_avg[t])

         # calc agv RPA
        avg_rpa = 0
        for i in range(len(RPA)):
            avg_rpa += RPA[i]
        avg_rpa /= len(RPA)

        time_axis = [x for x in range(self.startDay,self.endDay)]
        avg_curve = [avg_rpa for i in range(len(RPA))]

        plt.title('{2}\nRelative Power Average from day {0} to {1}'.format(self.startDay, self.endDay, self.resultfile))
        plt.plot(time_axis, RPA, 'ro', label='RPA')
        plt.plot(time_axis, avg_curve, 'r', label='avg RPA')
        plt.xlabel('Time [days]')
        plt.figtext(0.3,0.3,'avg RPA {0:.2f}'.format(avg_rpa, fontsize=12))
        plt.ylabel('RPA')
        plt.grid(True)
        plt.legend(loc='lower left', ncol=1)
        plt.show()

    def plot_relativePeakToAveragePower(self):
        """
        plot realtive peak to power average
        :return:
        """

        fluct_avg = []
        fluct_PtP = []
        rem_PtP = []
        rem_avg = []
        RPAP = []

        for d in range(self.endDay-self.startDay):

            fluct_avg = 0
            rem_avg = 0
            for t in range(len(self.fluctuation[d+self.startDay-1])):
                fluct_avg += (self.fluctuation[d+self.startDay-1][t] / self.stepsize)
                rem_avg += (self.remainder[d+self.startDay-1][t] / self.stepsize)

            fluct_avg /= len(self.fluctuation[d+self.startDay-1])
            rem_avg /= len(self.remainder[d+self.startDay-1])

            fluct_PtP.append(0)
            rem_PtP.append(0)

            fluct = self.fluctuation[d+self.startDay-1]
            rem = self.remainder[d+self.startDay -1]
            min_fluct = min(fluct)
            max_fluct = max(fluct)
            min_rem = min(rem)
            max_rem = max(rem)

            if(abs(min_rem) > abs(max_rem)):
                peak_rem = min_rem
            else:
                peak_rem = max_rem

            if(abs(min_fluct) > abs(max_fluct)):
                peak_fluct = min_fluct
            else:
                peak_fluct = max_fluct

            for t in range(len(self.fluctuation[d + self.startDay-1])):
                fluct_PtP[d] = peak_fluct/self.stepsize - fluct_avg
                rem_PtP[d] = peak_rem/self.stepsize - rem_avg

            if(fluct_PtP[d] != 0):
                RPAP.append(rem_PtP[d] / fluct_PtP[d])
            else:
                RPAP.append(99)

        # calc agv RPAP
        avg_rpa = 0
        for i in range(len(RPAP)):
            avg_rpa += RPAP[i]
        avg_rpa /= len(RPAP)

        time_axis = [x for x in range(self.startDay, self.endDay)]
        avg_curve = [avg_rpa for i in range(len(RPAP))]

        plt.title('{2}\nRelative Peak to Average Power from day {0} to {1}'.format(self.startDay, self.endDay, self.resultfile))

        bar_width = 0.7
        opacity = 0.5
        error_config={'ecolor': '0.3'}

       # plt.plot(time_axis, zeros, 'black')
        #plt.bar(time_axis, fluct_PtP, bar_width, alpha=opacity, color='r', label='sum fluctuation power peak to avg', error_kw=error_config)
        #plt.bar(time_axis, rem_PtP, bar_width, alpha=opacity, color='b', label='sum remainder power peak to avg', error_kw=error_config)
        plt.plot(time_axis, RPAP, 'ro', label='RPAP')
        plt.plot(time_axis, avg_curve, 'r', label='avg RPAP')
        plt.figtext(0.3,0.3,'avg RPAP {0:.2f}'.format(avg_rpa, fontsize=12))
        #plt.plot(time_axis, fluct_PtP, color='r', label='sum fluctuation power peak to avg')
        #plt.plot(time_axis, rem_PtP, color='b', label='sum remainder power peak to avg')
        plt.xlabel('Time [days]')
        plt.ylabel('power')
        plt.grid(True)
        plt.legend(loc='lower left', ncol=1)
        plt.show()

    def plot_relativePowerToAverage(self):
        """
        plot relative power to average power curve
        :return:
        """

        #fluct_avg = []
        fluct_PtP = []
        rem_PtP = []
        #rem_avg = []
        RPA = []

        for d in range(self.endDay-self.startDay):
            # calc avg powers in fluct and remainder for day d
            fluct_avg = (sum(self.fluctuation[d+self.startDay-1]) / len(self.fluctuation[d+self.startDay-1])) / self.stepsize
            rem_avg = (sum(self.remainder[d+self.startDay-1]) / len(self.remainder[d+self.startDay-1])) / self.stepsize

            sum_fluct_powerToAvg = 0
            sum_rem_powerToAvg = 0
            for t in range(len(self.fluctuation[d+self.startDay-1])):
                sum_fluct_powerToAvg += abs((self.fluctuation[d+self.startDay-1][t]/self.stepsize) - fluct_avg)
                sum_rem_powerToAvg += abs((self.remainder[d+self.startDay-1][t]/self.stepsize) - rem_avg)

            RPA.append(sum_rem_powerToAvg/sum_fluct_powerToAvg)



        # calc agv RPA
        avg_rpa = sum(RPA) / len(RPA)

        time_axis = [x for x in range(self.startDay, self.endDay)]
        avg_curve = [avg_rpa for i in range(len(RPA))]

        plt.title('{2}\nRelative Power-to-Average  from day {0} to {1}'.format(self.startDay, self.endDay, self.resultfile))

        plt.plot(time_axis, RPA, 'ro', label='RPA')
        plt.plot(time_axis, avg_curve, 'r', label='avg RPA')
        plt.figtext(0.3,0.3,'avg RPA {0:.2f}'.format(avg_rpa, fontsize=12))

        plt.xlabel('Time [days]')
        plt.ylabel('RPA')
        plt.grid(True)
        #plt.legend(loc='lower left', ncol=1)
        plt.show()


    def getAvgNumberOfSchedules(self):
        """
        :return: avg number of schedules
        """

        return (sum(self.avg_schedules) / len(self.avg_schedules))


    def getAvgRelPTV(self):
        """
        :return: avg rel PTV
        """

        avg_PTV_improvement = sum(self.maxmindiff_improvement) / len(self.maxmindiff_improvement)
        avg_PTV_improvement = 100.0 - avg_PTV_improvement
        avg_PTV_improvement /= 100.0

        return avg_PTV_improvement

    def getAvgRuntime(self):
        """
        :return: average runtime
        """
        return (sum(self.runtime) / len(self.runtime))

    def getSchedules(self, window):
        """

        :param window: window size of moving average
        :return: min, avg and max schedules + moving average of every size
        """
        avg_movingavg = self.movingavearage(self.avg_schedules, window)
        min_movingavg = self.movingavearage(self.min_schedules, window)
        max_movingavg = self.movingavearage(self.max_schedules, window)


        return [self.min_schedules,  min_movingavg, self.avg_schedules, avg_movingavg, self.max_schedules, max_movingavg]


    def getRemainder(self):
        """

        :return: remainder curves
        """

        return self.remainder[self.startDay-1:self.endDay]

    def getMessages(self):
        """

        :return: return number of messages curve
        """

        return self.msg_sent

    def getRPTV(self):
        """

        :return: relative PTV distance
        """

        RPTV = []
        print len(self.maxmindiff_improvement)
        for i in range(len(self.maxmindiff_improvement)):
            RPTV.append((100.0 - self.maxmindiff_improvement[i])/100.0)
            #RPTV.append((100.0 - self.maxmindiff_improvement[i])/100.0)

        return RPTV

    def getMessage_MovingAvg(self, window):
        """

        :param window: window size
        :return: moving average of messages

        """
        return self.movingavearage(self.msg_sent, window)

    def getRPTV_MovingAvg(self, window):
        """

        :param window: window size
        :return: moving average of RPTV
        """
        RPTV = []
        for i in range(len(self.maxmindiff_improvement)):
            RPTV.append((100.0 - self.maxmindiff_improvement[i])/100.0)


        return self.movingavearage(RPTV, window)

    def getAvgMessages(self):
        """

        :return: average number of messages
        """

        return sum(self.msg_sent) / len(self.msg_sent)

    def getLoadDuration_Remainder(self):
        """

        :return: load duration curve of remainder
        """

        energyremainder_curve = []

        if(self.endDay - self.startDay) == 0: #only one day
            energyremainder_curve = self.remainder[self.startDay-1]

        else:

            for d in range(self.endDay-self.startDay):

                energyremainder_curve.extend(self.remainder[d+self.startDay-1])
        # transform energy to power

        powerremainder_curve = [x / self.stepsize for x in energyremainder_curve]

        sorted_powerremainder_curve_view = reversed(sorted(powerremainder_curve))


        sorted_powerremainder_curve = []
        for remaindervalue in sorted_powerremainder_curve_view:
            sorted_powerremainder_curve.append(remaindervalue)

        return sorted_powerremainder_curve


    def getLoadDuration_Fluct(self):
        """

        :return: load duration curve of fluctuations
        """
        energyfluct_curve = []


        if(self.endDay - self.startDay) == 0: #only one day
            energyfluct_curve = self.fluctuation[self.startDay-1]

        else:
            for d in range(self.endDay-self.startDay):
                energyfluct_curve.extend(self.fluctuation[d+self.startDay-1])

        # transform energy to power
        powerfluct_curve = [x / self.stepsize for x in energyfluct_curve]



        sorted_powerfluct_curve_view = reversed(sorted(powerfluct_curve))

        sorted_powerfluct_curve = []
        for fluctvalue in sorted_powerfluct_curve_view:
            sorted_powerfluct_curve.append(fluctvalue)

        return sorted_powerfluct_curve

