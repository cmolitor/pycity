__author__ = 'Christoph Molitor'

import xlrd
import numpy as np
import os
from toolbox import chngResE as hp

class ElectricalLoad(object):
    """
    This class represents electrical loads as part of an apartment
    """
    bElectricalData = False  # boolean which is set true after the data which is unique for all instances is loaded
    SLP_electrical = 0  # in Wh

    def __init__(self, AnnualElectricalDemand, stepSize):
        # Read profiles which are valid for all houses only once
        """
        Constructor of ElectricalLoad
        :param AnnualElectricalDemand: annual electrical demand in kWh
        :param stepSize: duration of time slots in seconds
        """
        self.demandelectrical_annual = AnnualElectricalDemand
        self.scalingSLPel = self.demandelectrical_annual/1000

        if ElectricalLoad.bElectricalData == False:
            ElectricalLoad.bElectricalData = True
            # Read electrical standard load profiles
            script_dir = os.path.dirname(__file__)
            workbook = xlrd.open_workbook(script_dir + '/../data/SLP_electrical_H0_NRW.xlsx')
            worksheet = workbook.sheet_by_name("H0_NRW_15min")
            SLP_electrical_org = np.array([[x.value for x in worksheet.col(2, 1)], [x.value for x in worksheet.col(3, 1)]])

            ElectricalLoad.SLP_electrical = hp.changeResolutionEnergy(self, SLP_electrical_org, stepSize)

            # print(ElectricalLoad.SLP_electrical)

    def getAnnualElectricalDemand(self):
        """
        Annual electrical demand of the electrical load
        :return: annual electrical demand in kWh
        """
        return self.demandelectrical_annual

    def getElectricalDemandCurve(self, fromTime, toTime):
        """
        Method returns the electrical demand curve (in Ws) for a given time period
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: ndarray with (2x(toTime-fromTime)/Timestep); first row time in seconds; second row values
        """
        indFrom = min((np.asarray(np.where(ElectricalLoad.SLP_electrical[0, :] >= fromTime)))[0, :])
        indTo = max((np.asarray(np.where(ElectricalLoad.SLP_electrical[0, :] <= toTime)))[0, :]) + 1
        ret = np.zeros((2, indTo-indFrom))
        ret[0, :] = ElectricalLoad.SLP_electrical[0, indFrom:indTo]
        ret[1, :] = ElectricalLoad.SLP_electrical[1, indFrom:indTo] * self.scalingSLPel
        # print("self.scalingSLPel: ", self.scalingSLPel)
        # print(ret)
        # print("Scaling factor:", self.scalingSLPel)
        return ret
