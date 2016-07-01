__author__ = 'Christoph Molitor'

import numpy as np
import copy as cp


def changeResolutionEnergy(self, timeseries_org, stepSize_new):
    """
    Function to change the time scale of a given time series to the new time scale defined by stepSize_new.
    The original time resolution is extracted form the original time resolution of the time series as given
    in the first column of the vector.
    :param self:
    :param timeseries_org: original time series (first column of vector: time in seconds; second column: data (energy))
    :param stepSize_new: new time scale in seconds
    :return: data with changed time scale (first column of vector: time in seconds; second column: data (energy))
    """
    _stepSize_org = timeseries_org[0, 1] - timeseries_org[0, 0]  # extract original data resolution
    _startTime_org = timeseries_org[0, 0]  # extract original start time, e.g. 0s
    _endTime_org = max(timeseries_org[0, :])  # extract original end time

    # create a new time vector with the new resolution
    _vecTime_new = np.arange(_startTime_org, _endTime_org, stepSize_new)
    _vecValues_new = cp.deepcopy(_vecTime_new)

    i = 0
    for _step in range(0, len(_vecTime_new)):
        _startTime_new = _vecTime_new[_step]
        _endTime_new = _startTime_new + stepSize_new
        if _endTime_new > _endTime_org:
            _endTime_new = _endTime_org
        # print(_startTime_new, _endTime_new - _startTime_new)

        # search for startTime in old time vector
        while timeseries_org[0, i] <= _startTime_new:
            i = i + 1
        _lowerStartTime = timeseries_org[0, i - 1]

        # search for endtime in old time vector
        y = cp.deepcopy(i)
        while timeseries_org[0, y] < _endTime_new:
            y = y + 1
        # _lowerEndTime = SLP_electrical_org[0, y-1]
        _upperEndTime = timeseries_org[0, y]

        # print("res: ", i-1, y, _lowerStartTime, " <= ", _startTime_new, "<=", _endTime_new, "<= ", _upperEndTime)

        energy_old = sum(timeseries_org[1, (i - 1):y])
        energy_lowerend = (_startTime_new - _lowerStartTime) / _stepSize_org * timeseries_org[1, i - 1]
        energy_upperend = (_upperEndTime - _endTime_new) / _stepSize_org * timeseries_org[1, y - 1]
        energy_new = energy_old - energy_lowerend - energy_upperend
        _vecValues_new[_step] = energy_new
        # print("Energy:", energy_old, energy_new)

    timeseries_new = np.zeros((2, len(_vecTime_new[:])))
    timeseries_new[0, :] = _vecTime_new[:]
    timeseries_new[1, :] = _vecValues_new[:]

    # print(timeseries_new)

    return timeseries_new