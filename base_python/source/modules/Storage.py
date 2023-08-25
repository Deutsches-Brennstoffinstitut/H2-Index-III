#  imports
import math

from base_python.source.modules.GenericUnit import GenericUnit
from base_python.source.helper._FunctionDef import range_limit
from base_python.source.helper._FunctionDef import in_range
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import GenericTechnicalInput
from numpy import array
import logging


class Storage(GenericUnit):
    """Create a Storage object with output=electric
    use Set_ControlledByConsumption() to use it as controlled node"""

    def __init__(self, size=None, charge_power=math.inf, technology=None, active=False, initial_value=None,
                 efficiency: float = 1.0, new_investment=False, economical_parameters=None, stream_type=None,
                 generic_technical_input: GenericTechnicalInput = None):
        """
        :param size:          define a) size as single value with no in and output-flow limitation or b) list [size, charging capability, discharge capability]
        :param technology:    type of installation
        :param controlled_medium:  type of consumption ('electric', 'h2', 'heat', ...)
        :param active:        True if storage controlled by profile
        :param initial_value: set the fill level of buffer at first run, None=unlimited energy
        :param efficiency:    net efficiency for the charge and discharge process
        """
        super().__init__(size=size, technology=technology, active=active, new_investment=new_investment,
                         economical_parameters=economical_parameters, stream_type=stream_type,
                         generic_technical_input=generic_technical_input)
        # rewrite inherited variables

        # set class specific variables
        self.charge_power = charge_power
        self.efficiency = efficiency

        self.component_technical_results.component_history['storage_level'] = []
        # set module specific variables
        self.buffer_profile = []
        self.buffer_init = 0 if initial_value is None else initial_value
        self.buffer_old = 0 if initial_value is None else initial_value
        self.buffer_new = 0 if initial_value is None else initial_value
        self.runcount_old = 0

    def power_to_energy(self, value):
        return value * self.time_resolution / 60

    def energy_to_power(self, value):
        return value * 60 / self.time_resolution

    def set_initial_value(self, buffer):
        self.buffer_init = buffer
        self.set_properties()

    #############################
    # Module specific functions #
    #############################

    def get_load(self):
        """
        :return: string
        """
        return f"aktueller Flow {self.ports[self.controlled_medium]} kW mit aktuellem Füllstand {self.buffer_new} kWh, Status: {self.status}"


"""
    def check_Status(self):
        return "{}-Anlage mit {} kW Leistung {}".format(self.type, self.scaling, self.status)

    def calc_InvestCost(self):
        print('you wish')

    def calc_OperationalCost(self):
        print('you wish')

    def calc_Efficiency(self):
        current_efficiency = 0.75
        return current_efficiency
"""

if __name__ == '__main__':
    print('T E S T: Storage')
    My_Plant = Storage(size=[10, -1, 2], controlled_medium='electric', initial_value=5)
    input = {'electric': 5}
    My_Plant.run(myInputs=input, runcount=0)
    print(My_Plant.get_load())
    My_Plant.run(myInputs=input, runcount=1)
    print(My_Plant.get_load())
    My_Plant.run(myInputs=input, runcount=2)
    print(My_Plant.get_load())
    My_Plant.run(myInputs=input, runcount=3)
    print(My_Plant.get_load())
    My_Plant.run(myInputs=input, runcount=4)
    print(My_Plant.get_load())
    My_Plant.run(myInputs=input, runcount=5)
    print(My_Plant.get_load())
    My_Plant.run(myInputs=input, runcount=6)
    print(My_Plant.get_load())
    My_Plant.run(myInputs=input, runcount=7)
    print(My_Plant.get_load())
    # try:
    #    My_Plant.set_priority('heaat')
    #    print('wrong priority port: has been accepted')
    # except:
    #    print('test failed successfully')
