__author__ = 'Christoph Molitor'

from building.apartment import Apartment

import aiomas


class BuildingAgent(aiomas.Agent):
    def __init__(self, container, name, iApartments, sqm, specDemandTh, stepSize):
        # todo: if iApartments == 0 -> break
        """
        Constructor of Building
        :param iApartments: number of apartments within the building
        :param sqm: square meter (sqm) of each apartment in the building [m^2]
        :param specDemandTh: specific thermal demand per sqm and year [kWh/(m^2 a)]
        :param stepSize: size of time slot in seconds
        """
        super().__init__(container, name)

        self.iApartments = iApartments
        self.listApartments = list()

        if self.iApartments == 1:
            self.buildingType = 1
        else:
            self.buildingType = 2

        for x in range(0, iApartments):
            self.listApartments.append(Apartment(self.buildingType, sqm, specDemandTh, stepSize))
            # print("Apartment created")

    def getAnnualThermalDemand(self):
        """
        Method returns the aggregated annual thermal demand of the building (sum of all apartments)
        :return: aggregated annual thermal demand in kWh
        """
        _demandthermal_annual = 0
        for x in range(0, len(self.listApartments)):
            _demandthermal_annual += self.listApartments[x].getAnnualThermalDemand()
        return _demandthermal_annual

    def getThermalDemandCurve(self, fromTime, toTime):
        """
        Method returns the thermal demand curve (in Ws) for a given time period
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: ndarray with (2x(toTime-fromTime)/Timestep); first row time in seconds; second row values
        """
        _thermalDemandCurve = self.listApartments[0].getThermalDemandCurve(fromTime, toTime)
        for x in range(1, len(self.listApartments)):
            _thermalDemandCurve[1, :] += self.listApartments[x].getThermalDemandCurve(fromTime, toTime)[1, :]
        return _thermalDemandCurve

    def getAnnualElectricalDemand(self):
        """
        Annual electricity consumption of the whole building
        :return: annual electrical demand in kWh
        """
        _demandelectrical_annual = 0
        for x in range(0, len(self.listApartments)):
            _demandelectrical_annual += self.listApartments[x].getAnnualElectricalDemand()
        return _demandelectrical_annual

    def getElectricalDemandCurve(self, fromTime, toTime):
        """
        Method returns the electrical demand curve (in Ws) for a given time period and for the whole building
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: ndarray with (2x(toTime-fromTime)/Timestep); first row time in seconds; second row values
        """
        _electricalDemandCurve = self.listApartments[0].getElectricalDemandCurve(fromTime, toTime)
        for x in range(1, len(self.listApartments)):
            _electricalDemandCurve[1, :] += self.listApartments[x].getElectricalDemandCurve(fromTime, toTime)[1, :]
        return _electricalDemandCurve