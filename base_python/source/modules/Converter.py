#  imports
import logging

from base_python.source.modules.GenericUnit import GenericUnit
import base_python.source.basic.ModelSettings as Settings
# from base.source.helper._FunctionDef import range_limit
from base_python.source.basic.Streamtypes import StreamEnergy, StreamMass, StreamDirection
from base_python.source.basic.Units import Unit
from base_python.source.basic.Quantities import PhysicalQuantity
from scipy import interpolate, optimize
from functools import lru_cache
from enum import Enum, auto
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import GenericTechnicalInput
import numpy as np
import math

class Converter(GenericUnit):

    class Technology(Enum):
        Methanation = auto()
    def __init__(self, size=None, technology=None, active=False, new_investment=False,
                 economical_parameters=None, generic_technical_input: GenericTechnicalInput = None):
        """

        :param size:                    installed nominal "power"
        :param technology:              type of installation
        :param active:                  True if the component controls the system
        :param new_investment:          True if CAPEX shall be included in balance
        :param economical_parameters:   see model_base/dataclasses for more info
        :param generic_technical_input: see model_base/dataclasses for more info
        """
        super().__init__(size=size, technology=technology, active=active,
                         new_investment=new_investment,
                         economical_parameters=economical_parameters,
                         generic_technical_input=generic_technical_input)  # initialize class generic unit
        # set inherited variables
        self.size = size
        self.possible_streams = {}
        self.value_calculation = {}
        self.interpolation_functions = {}
        self.inverted_interp_function = {}

    def run(self, port_id, branch_information, runcount=0):

        """
        Run method of the converter which is called by the branch object while solving

        Args:
            port_id (str): ID of the branch connected port
            branch_information (dict): Information about the branch state at the runcount that includes (pressure, temperature, fraction, stream)
            runcount (int): Runcount of the model for which the component has to be solved

        """

        self.status = 0  # set default status with 0:ok; >0:warning; <0:error

        # check whether a connected port has a stream profile

        if self.controlled_port != None:
            port = self.controlled_port
        else:
            port = self.get_port_by_id(port_id)

        # check if control strategy is temporarily changed
        [controlled_port, port_value, loop_control] = self._calc_control_var(port,
                                                                             branch_information[
                                                                                 PhysicalQuantity.stream])

        if self.active & (not loop_control):  # so we can use the nominal load or a set profile
            if controlled_port.get_profile_values(runcount) is None:  # no profile set
                if controlled_port.get_stream_limits() is None:
                    controlled_port.set_stream(runcount, 0)  # not running at all
                else:
                    controlled_port.set_stream(runcount, controlled_port.get_stream_limits()[1])  # set to max
            elif PhysicalQuantity.stream not in controlled_port.get_profile_values(runcount):
                if controlled_port.get_stream_limits() is None:
                    controlled_port.set_stream(runcount, 0)  # not running at all
                else:
                    controlled_port.set_stream(runcount, controlled_port.get_stream_limits()[1])  # set to max
            else:
                controlled_port.set_profile_stream(runcount)
        else:
            controlled_port.set_stream(runcount, port_value)
        try:

            # load = self._get_load_by_inverted_interp(port.get_type(), port.get_stream_type(),
            #                                         port.get_stream())
            load = self._get_load_by_inverted_interp(controlled_port.get_type(), controlled_port.get_stream_type(),
                                                     controlled_port.get_stream())

        except:
            logging.critical(f'Error at converter load calculation at runcount {runcount}')
        for port in self.ports.values():
            if not port == controlled_port:
                if (port.get_type(), port.get_stream_type()) in self.possible_streams:
                    single_port_value = self._get_stream_by_load_interp(port.get_type(), port.get_stream_type(),
                                                                        load)
                    port.set_stream(runcount, single_port_value)

    #############################
    # Module specific functions #
    ############################

    @lru_cache(100)
    def _get_stream_by_load_interp(self, port_type=PhysicalQuantity, stream_type=StreamEnergy, load=0):
        return self.possible_streams[(port_type, stream_type)](load).min()

    @lru_cache(100)
    def _get_load_by_inverted_interp(self, port_type=PhysicalQuantity, stream_type=StreamEnergy, stream_value=0):
        return self.inverted_interp_function[(port_type, stream_type)](stream_value).min()

    def _set_possible_streams(self, load_range=range(0, 101, 1)):
        #todo: dokumentieren
        #todo: kucken wo die überall vererbt wird und die loadrange jeweils auslesen. Bisher: CHP_Plant und Electrolyser

        load = load_range
        load_dependend_efficiencies = {}
        stream_limits = {}
        min_val = 0
        max_val = 0
        for single_load in load:
            for key, value in self.value_calculation.items():
                resulting_stream_value = value(single_load) * self.size
                if key not in load_dependend_efficiencies:
                    load_dependend_efficiencies[key] = [resulting_stream_value]
                else:
                    load_dependend_efficiencies[key].append(resulting_stream_value)

        for key, value in load_dependend_efficiencies.items():
            affected_ports = self.get_ports_by_type(key[0])
            filtered_list = list(filter(lambda x: x != 0, load_dependend_efficiencies[key]))
            for single_port in affected_ports:
                if len(filtered_list) > 0:
                    single_port.update_stream_limit((min(filtered_list), max(filtered_list)))
                else:
                    single_port.update_stream_limit((0, 0))
            self.inverted_interp_function[key] = interpolate.interp1d(value, load)
            load_dependend_efficiencies[key] = interpolate.interp1d(load, value)

        self.possible_streams = load_dependend_efficiencies

        self._get_stream_by_load_interp.cache_clear()
        self._get_load_by_inverted_interp.cache_clear()

    def get_efficiency_at_reference_load(self, stream_type, load):
        efficiencies = [i for i in self.efficiencies.all_efficiencies if i.get_medium_calculated() == stream_type]
        if len(efficiencies) > 1:
            logging.critical(
                f'More than one efficiency given for calculation of {stream_type} in {self.__class__.__name__}')
        elif len(efficiencies) == 1:
            efficiency = efficiencies[0].get_interpolation_function()
            return float(efficiency(load))
        else:
            return 0
    # set limits for all ports
