#  imports
import logging
import math

from base_python.source.modules.GenericUnit import GenericUnit
from base_python.source.helper._FunctionDef import range_limit
from base_python.source.model_base.Port_Mass import Port_Mass
from base_python.source.basic.Streamtypes import StreamEnergy, StreamMass
from base_python.source.basic.Units import Unit
from base_python.source.basic.Quantities import PhysicalQuantity
from base_python.source.basic.Streamtypes import StreamDirection
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import *
from base_python.source.model_base.Dataclasses.EconomicalDataclasses import *
from typing import List
from enum import Enum, auto


class Source(GenericUnit):
    class Technology(Enum):
        WIND_ONSHORE = auto()  # creates string from parameter name
        PV_OPEN_AREA = auto()
        PV_ROOF = auto()

    def __init__(self, stream_type=None, size=None, technology=None, active=False, new_investment=False,
                 economical_parameters: EconomicalParameters = None, generic_technical_input: GenericTechnicalInput = None):
        """

        :param stream_type:             of types StreamMass, or StreamEnergy
        :param size:                    installed Nameplate Power, should be in kW or kg
        :param technology:              type of installation ('pv', 'wind', 'grid')
        :param active:                  True if the component controls the system
        :param new_investment:          True if CAPEX shall be included in balance
        :param economical_parameters:   see model_base/dataclasses for more info
        :param generic_technical_input: see model_base/dataclasses for more info
        """
        super().__init__(size=size, technology=technology, active=active, new_investment=new_investment,
                         economical_parameters=economical_parameters, stream_type=stream_type,
                         generic_technical_input=generic_technical_input)  # initialize class generic unit

        self._add_port(port_type=stream_type, component_ID=self.component_id, fixed_status=active, sign=StreamDirection.stream_out_of_component)

        if self.size != None:
            self.ports[self.port_types[self.stream_type][0]].set_stream_limit((0, self.size))
        else:
            self.ports[self.port_types[self.stream_type][0]].set_stream_limit((0, math.inf))

    def set_properties(self):
        """
        This function is called when properties of the component change and have to be updated

        """
        output_port = self.get_ports_by_type_and_sign(self.stream_type, StreamDirection.stream_out_of_component)
        if self.size != None:
            output_port.update_stream_limit((0, self.size))
        else:
            output_port.update_stream_limit((0, math.inf))

    def run(self, port_id, branch_information, runcount=0):
        """ runs the module, sets values of output ports
        :param myInputs: placeholder for input parameters
        :param runcount: Step Index (runtime = runcount * resolution)
        """

        self.status = 0  # set default status with 0:ok; >0:warning; <0:error

        # check whether a connected port has a stream profile

        if self.controlled_port != None:
            port = self.controlled_port
        else:
            port = self.get_port_by_id(port_id)

        # check if control strategy is temporarily changed
        [controlled_port, port_value, loop_control] = self._calc_control_var(port, branch_information[
            PhysicalQuantity.stream])

        if self.active & (not loop_control):
            if controlled_port.get_profile_values(runcount) is None or \
                    PhysicalQuantity.stream not in controlled_port.get_profile_values(runcount):
                controlled_port.set_stream(runcount, 0) \
                    if controlled_port.get_stream_limits() is None \
                    else controlled_port.set_stream(
                    runcount, controlled_port.get_stream_limits()[1])
            else:
                controlled_port.set_profile_stream(runcount)
        else:
            if loop_control:
                controlled_port.set_stream(runcount, port_value)
            else:
                port.set_stream(runcount, port.get_stream_limited_value(port_value))

        # set operation state
        # self.operation = self.ports[controlled_medium] != 0

    #############################
    # Module specific functions #
    #############################
