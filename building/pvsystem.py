__author__ = 'Annika Wierichs'

class PVSystem(object):

    def __init__(self, env, annualGeneration):

        self.environment = env                      # environment of the PV system
        self.annualGeneration = annualGeneration    # annual energy generation of PV system in kWh

        self.addPVSystemToEnvironment()             # add created pv system to respective environment


    def addPVSystemToEnvironment(self):
        """
        add the pv system to its environment to make sure that the internal and external solar generation values are
        updated accordingly in environment
        """
        self.environment.addDomesticPVSystem(self.getAnnualGeneration())

    def deletePVSystemFromEnvironment(self):
        """
        delete the pv system from its environment to make sure that the internal and external solar generation values
        are updated accordingly in environment
        """
        self.environment.deleteDomesticPVSystem(self.getAnnualGeneration())

    def getGenerationCurve(self, fromTime, toTime):
        """
        returns the energy produced during each time step within the range fromTime to toTime (negative values)
        stepSize is defined by the environment
        :param fromTime: from time
        :param toTime: to time
        :return: curve of PV energy generation for defined time period in Ws (2 x timesteps array) including time
        """
        # get energy curve (depending on annual generation of the system) from environment
        return self.environment.getLclPVEnergyCurve(fromTime, toTime, self.getAnnualGeneration())


    # ------------------------------------------------------------------------------------------------------------------
    # set & get

    def getEnvironment(self):
        return self.environment
    def setEnvironment(self, environment):
        self.environment = environment

    def getAnnualGeneration(self):
        return self.annualGeneration
    def setAnnualGeneration(self, ag):
        self.annualGeneration = ag