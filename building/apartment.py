__author__ = 'Christoph Molitor'

import xlrd
import numpy as np
from building.electricalload import ElectricalLoad
import os
from toolbox import chngResE as hp

class Apartment(ElectricalLoad):
    """
    The class apartment represents an apartment within a building. A building has at least one apartment but can have also
    a larger number of apartments.
    """
    bThermalData = False  # boolean which is set true after the data which is unique for all instances is loaded
    SLP_thermal_SFH = 0  # thermal standard load profile for single family house standardized to 1000kWh/a in Wh
    SLP_thermal_MFH = 0  # thermal standard load profile for multi family house standardized to 1000kWh/a in Wh

    def __init__(self, buildingType, sqm, specDemandTh, stepSize):
        """
        Constructor of apartment
        :param buildingType: 1=Single family house (SFH); else=Multi-family house (MFH)
        :param sqm: square meter of the apartment [m^2]
        :param specDemandTh: specific thermal demand per sqm [kWh/(m^2 a)]
        :param stepSize: duration of time slots in seconds
        """
        self.buildingType = buildingType
        self.sqm = float(sqm)  # in sqm
        self.specDemandTh = float(specDemandTh)  # in kWh/(sqm a)

        # Calculation of annual electrical energy consumption according to
        # [1]B. Schlomann, E. Gruber, W. Eichhammer, N. Kling, J. Diekmann, H.-J. Ziesing, H. Rieke, F. Wittke,
        # T. Herzog, M. Barbosa, S. Lutz, U. Broeske, D. Merten, D. Falkenberg, M. Nill, M. Kaltschmitt, B. Geiger,
        # H. Kleeberger, und R. Eckl,
        # Energieverbrauch der privaten Haushalte und des Sektors Gewerbe, Handel, Dienstleistungen (GHD),
        # Fraunhofer ISI, Apr. 2004.
        # data for former west Germany; average value 31.7 kWh/sqm/a
        super(Apartment, self).__init__(31.7 * self.sqm, stepSize)
        # Read profiles which are valid for all houses only once
        if Apartment.bThermalData == False:
            Apartment.bThermalData = True
            script_dir = os.path.dirname(__file__)

            # Read thermal demand profiles for SFH
            workbook = xlrd.open_workbook(script_dir + '/../data/SLP_thermal_SFH.xlsx')
            worksheet = workbook.sheet_by_name('Tabelle1')
            SLP_thermal_SFH_org = np.array([[x.value for x in worksheet.col(1, 1)], [x.value for x in worksheet.col(3, 1)]])
            Apartment.SLP_thermal_SFH = hp.changeResolutionEnergy(self, SLP_thermal_SFH_org, stepSize)
            # print(Apartment.SLP_thermal_SFH)

            # Read thermal demand profiles for MFH
            workbook = xlrd.open_workbook(script_dir + '/../data/SLP_thermal_MFH.xlsx')
            worksheet = workbook.sheet_by_name('Tabelle1')
            SLP_thermal_MFH_org = np.array([[x.value for x in worksheet.col(1, 1)], [x.value for x in worksheet.col(3, 1)]])
            Apartment.SLP_thermal_MFH = hp.changeResolutionEnergy(self, SLP_thermal_MFH_org, stepSize)
            # print(Apartment.SLP_thermal_MFH)

        self.demandthermal_annual = self.sqm * self.specDemandTh  # in kWh
        self.scalingSLPth = self.demandthermal_annual/1000

    # returns annual thermal demand of the apartment
    def getAnnualThermalDemand(self):
        """
        Method returns the aggregated annual thermal demand of the apartment
        :return: aggregated annual thermal demand in kWh
        """
        return self.demandthermal_annual

    # returns time series of electrical demand for this apartment
    def getThermalDemandCurve(self, fromTime, toTime):
        """
        Method returns the thermal demand curve (in Ws) for a given time period
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: ndarray with (2x(toTime-fromTime)/Timestep); first row time in seconds; second row values
        """
        if self.buildingType == 1:
            SLP_thermal = Apartment.SLP_thermal_SFH
        else:
            SLP_thermal = Apartment.SLP_thermal_MFH

        indFrom = min((np.asarray(np.where(SLP_thermal[0, :] >= fromTime)))[0, :])
        indTo = max((np.asarray(np.where(SLP_thermal[0, :] <= toTime)))[0, :]) + 1
        ret = np.zeros((2, indTo-indFrom))
        ret[0, :] = SLP_thermal[0, indFrom:indTo]
        ret[1, :] = SLP_thermal[1, indFrom:indTo] * self.scalingSLPth  # scale SLP to actual consumption
        #print("SLPsclaing:", self.scalingSLPth)
        return ret
