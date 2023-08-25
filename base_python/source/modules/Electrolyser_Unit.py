#  imports
import pandas as pd
import sys

from base_python.source.modules.GenericUnit import GenericUnit
from base_python.source.modules.Electrolyser import Electrolyser
from base_python.source.basic import ModelSettings
from base_python.source.modules.Converter import Converter
from base_python.source.modules.Consumer import Consumer
from base_python.source.basic.Streamtypes import *
from base_python.source.basic.Units import Unit
from base_python.source.basic.Quantities import PhysicalQuantity
from base_python.source.model_base.Dataclasses.EconomicalDataclasses import *
from base_python.source.model_base.Port_Mass import Port_Mass
from base_python.source.model_base.Port import Port
from base_python.source.helper._FunctionDef import range_limit
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import GenericTechnicalInput
import logging
from dataclasses import dataclass
from scipy import interpolate
import numpy as np
import math
from enum import Enum, auto


class Electrolyser_Unit(GenericUnit):
    class PortIdentifiers(Enum):
        BOP = auto()
        MainElectricInput = auto()

    @dataclass
    class SpecifyBalanceOfPlant:
        power_consumption_BOP_standby: float
        power_consumption_BOP_operating: float
        unit_power: Unit.kW

        def get_power_consumption_standby(self):
            """

            Returns:
                Power consumption for balance of plant of the ely unit at standby
            """
            return self.power_consumption_BOP_standby

        def get_power_consumption_operating(self):
            """

            Returns:
                Power consumption for balance of plant of the ely unit at operating
            """
            return self.power_consumption_BOP_operating

    def __init__(self, base_electrolyser: Electrolyser, variable_electrolyser: Electrolyser,
                 specify_balance_of_plant: SpecifyBalanceOfPlant = None, active=False,
                 economical_parameters: EconomicalParameters = None):
        super().__init__(active=active, economical_parameters=economical_parameters)

        self.port_link_dataframe = pd.DataFrame()
        self.bop_port = None
        self.base_ely = base_electrolyser
        self.variable_ely = variable_electrolyser

        if specify_balance_of_plant is not None:
            self.bop_specifications = specify_balance_of_plant
            self.bop_port = self._add_port(port_type=StreamEnergy.ELECTRIC,
                                           component_ID=self.component_id,
                                           fixed_status=True,
                                           sign=StreamDirection.stream_into_component,
                                           unit=specify_balance_of_plant.unit_power,
                                           external_identifier=Electrolyser_Unit.PortIdentifiers.BOP)

        main_electric_port = self._add_port(port_type=StreamEnergy.ELECTRIC,
                                            component_ID=self.component_id,
                                            fixed_status=True,
                                            sign=StreamDirection.stream_into_component,
                                            unit=specify_balance_of_plant.unit_power,
                                            external_identifier=Electrolyser_Unit.PortIdentifiers.MainElectricInput)

        for electrolyser in [base_electrolyser, variable_electrolyser]:
            self.set_sub_component(electrolyser, electrolyser.get_technology().value)
            for port_id, single_port in electrolyser.get_ports().items():
                if not single_port.get_type() is StreamEnergy.ELECTRIC:
                    found_outter_port = self.get_ports_by_type_and_sign(single_port.get_type(), single_port.get_sign())
                else:
                    found_outter_port = main_electric_port
                if found_outter_port is None:
                    found_outter_port = self._add_port(port_type=single_port.get_type(),
                                                       component_ID=self.component_id,
                                                       fixed_status=single_port.get_fixed_status(),
                                                       sign=single_port.get_sign(),
                                                       unit=single_port.get_stream_unit())
                if found_outter_port not in self.port_link_dataframe.columns:
                    self.add_port_link(found_outter_port, electrolyser, single_port)
                elif single_port not in self.port_link_dataframe[found_outter_port]:
                    self.add_port_link(found_outter_port, electrolyser, single_port)

        pass

    def add_port_link(self, outter_port, component_name, inner_port):
        self.port_link_dataframe.at[component_name, outter_port] = inner_port

    def get_size(self):
        sizes = {}
        for name, sub_component in self.sub_components.items():
            sizes[name] = sub_component.get_size()
        return sizes

    def set_size(self, new_sizes: dict):
        for name, value in new_sizes.items():
            if name in self.sub_components:
                self.sub_components[name].set_size(value)
            else:
                logging.critical(f'Could not set size for Electrolyser unit, because {name} not in sub_components')
        self.set_properties()

    def set_properties(self):
        """
        This function is used to adapt the port

        """

        for sub_component in self.sub_components.values():
            sub_component.set_properties()
        for outter_port, inner_ports in self.port_link_dataframe.iteritems():
            outter_port.reset_stream_limits()
            for single_inner_port in inner_ports:
                outter_stream_limit = outter_port.get_stream_limits()
                inner_stream_limit = single_inner_port.get_stream_limits()
                if inner_stream_limit is not None:
                    if outter_stream_limit is None:
                        outter_port.set_stream_limit(inner_stream_limit)
                    else:
                        new_limit = (outter_port.get_sign().value *
                                     min(abs(outter_stream_limit[0]), abs(inner_stream_limit[0])),
                                     outter_stream_limit[1] + inner_stream_limit[1])
                        outter_port.update_stream_limit(new_limit)

        efficiency_base_wo_bop = self.base_ely._get_efficiency_dataframe(medium_referenced=StreamEnergy.ELECTRIC,
                                                                    medium_calculated=StreamMass.HYDROGEN)
        efficiency_variable_wo_bop = self.variable_ely._get_efficiency_dataframe(medium_referenced=StreamEnergy.ELECTRIC,
                                                                    medium_calculated=StreamMass.HYDROGEN)

        efficiency_input_base = self.base_ely.efficiencies.get_efficiencies_at_load()
        efficiency_input_variable = self.variable_ely.efficiencies.get_efficiencies_at_load()
        if isinstance(efficiency_input_base, pd.Series):
            self.efficiency_base_with_BOP = efficiency_base_wo_bop * pd.Series(data=self.base_ely.get_size() * efficiency_base_wo_bop.index / 100 / (
            abs(self.bop_specifications.get_power_consumption_operating()) + self.base_ely.get_size() * efficiency_base_wo_bop.index/100), index=efficiency_base_wo_bop.index)
        if isinstance(efficiency_input_variable, pd.Series):
            self.efficiency_variable_with_BOP = efficiency_variable_wo_bop * pd.Series(data=self.variable_ely.get_size() * efficiency_variable_wo_bop.index / 100 / (
            abs(self.bop_specifications.get_power_consumption_operating()) + self.variable_ely.get_size() * efficiency_variable_wo_bop.index/100), index=efficiency_variable_wo_bop.index)

    def get_sub_component_port(self, sub_component_name, main_port):
        if main_port in self.port_link_dataframe.columns:
            resulting_port = self.port_link_dataframe[main_port].loc[sub_component_name]
            return resulting_port
        else:
            logging.critical(
                f'Could not find desired sub component port for {self.__class__.__name__} of types {main_port.get_type()}')

    def get_all_linked_ports(self, main_port):
        resulting_ports = self.port_link_dataframe[main_port]
        return resulting_ports

    def check_properties_except_stream(self, port_list):
        properties_to_check = None
        for single_port in port_list:
            if properties_to_check is None:
                properties_to_check = single_port.get_all_properties()
                properties_to_check.pop(PhysicalQuantity.stream)
            else:
                check_against = single_port.get_all_properties()
                check_against.pop(PhysicalQuantity.stream)
                if not properties_to_check == check_against:
                    logging.warning(f'Sub components of component {self.name} do not have matching port properties')
                    sys.exit()

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
        [controlled_port, port_value, loop_control] = self._calc_control_var(port, branch_information[
            PhysicalQuantity.stream])

        if self.active & (not loop_control):
            if controlled_port.get_profile_values(runcount) is None:
                controlled_port.set_stream(runcount, 0) if controlled_port.get_stream_limits() is None \
                    else controlled_port.set_stream(runcount, controlled_port.get_stream_limits()[1])
            elif PhysicalQuantity.stream not in controlled_port.get_profile_values(runcount):
                controlled_port.set_stream(runcount, 0) if controlled_port.get_stream_limits() is None \
                    else controlled_port.set_stream(runcount, controlled_port.get_stream_limits()[1])
            else:
                controlled_port.set_profile_stream(runcount)
        else:
            if loop_control:
                controlled_port.set_stream(runcount, port_value)
            else:
                controlled_port.set_stream(runcount, port_value)

        port_value = controlled_port.get_stream()

        linked_base_ely_port = self.get_sub_component_port(self.base_ely, controlled_port)
        linked_variable_ely_port = self.get_sub_component_port(self.variable_ely, controlled_port)
        min_stream_base = linked_base_ely_port.get_stream_limits()[0]
        min_stream_variable = linked_variable_ely_port.get_stream_limits()[0]

        efficiency_input_base = self.base_ely.efficiencies.get_efficiencies_at_load()
        if isinstance(efficiency_input_base, pd.Series):
            opt_workpoint_stream_base = self.base_ely.get_size()* self.base_ely.value_calculation[(StreamEnergy.ELECTRIC, StreamTypes.power)](self.efficiency_base_with_BOP.idxmax())

        efficiency_input_variable = self.variable_ely.efficiencies.get_efficiencies_at_load()
        if isinstance(efficiency_input_variable, pd.Series):
            opt_workpoint_stream_variable = self.variable_ely.get_size() * -0.33 #self.variable_ely.value_calculation[(StreamEnergy.ELECTRIC, StreamTypes.power)](self.efficiency_variable_with_BOP.idxmax())

        else:
            opt_workpoint_stream_base = min_stream_base
            opt_workpoint_stream_variable = min_stream_variable
        min_stream_variable = linked_variable_ely_port.get_stream_limits()[0]
        max_workpoint_variable = linked_variable_ely_port.get_stream_limits()[1]
        resulting_streams = {}

        # TODO: Funktion auslagern nach oben input darf nur port_value + controlled_port sein

        # Input < Mindestlast -> kein Ely läuft
        if abs(port_value) < abs(min_stream_base) and abs(port_value) < abs(min_stream_variable):
            resulting_streams[self.base_ely] = 0
            resulting_streams[self.variable_ely] = 0
            controlled_port.set_stream(runcount, 0)
            port_value = 0

            # ML variabel < Input < (AP variable + ML Base) -> variabel nimmt Input
        elif abs(port_value) < abs(opt_workpoint_stream_variable + min_stream_base):
            resulting_streams[self.base_ely] = 0
            resulting_streams[self.variable_ely] = port_value

            # (AP var + ML Base) < Input < (Arbeitspunkt base + AP var) -> var auf optimum, base nimmt rest
        elif abs(port_value) >= abs(min_stream_base + opt_workpoint_stream_variable) and abs(port_value) <= abs(opt_workpoint_stream_variable + opt_workpoint_stream_base):
            resulting_streams[self.base_ely] = port_value - opt_workpoint_stream_variable
            resulting_streams[self.variable_ely] = opt_workpoint_stream_variable

            # (AP var + AP base) < Input < (max variabel + AP base) -> base auf AP, variabel nimmt Rest
        elif abs(port_value) >= abs(opt_workpoint_stream_variable + opt_workpoint_stream_base) and abs(port_value) <= abs(max_workpoint_variable + opt_workpoint_stream_base):
            resulting_streams[self.base_ely] = opt_workpoint_stream_base
            resulting_streams[self.variable_ely] = port_value - opt_workpoint_stream_base

            # Input > (AP base + max variabel) -> variabel nimmt max, base nimmt rest
        elif abs(port_value) > abs(max_workpoint_variable + opt_workpoint_stream_base):
            resulting_streams[self.variable_ely] = max_workpoint_variable
            resulting_streams[self.base_ely] = port_value - max_workpoint_variable
        for electrolyser, value in resulting_streams.items():
            connected_sub_component_port = self.get_sub_component_port(electrolyser, controlled_port)
            electrolyser.run(connected_sub_component_port.get_id(),
                             {PhysicalQuantity.stream: value},
                             runcount)

        if self.bop_port is not None:
            if controlled_port.get_stream() == 0:
                self.bop_port.set_stream(runcount, self.bop_specifications.get_power_consumption_standby())
            else:
                self.bop_port.set_stream(runcount, self.bop_specifications.get_power_consumption_operating())

        for port, linked_ports in self.port_link_dataframe.iteritems():
            port_stream = 0
            self.check_properties_except_stream(list(linked_ports))
            port.set_all_properties(runcount, linked_ports[0])
            for single_linked_port in linked_ports:
                port_stream += single_linked_port.get_stream()
            port.set_stream(runcount, port_stream)
            if port.get_stream() != port_stream:
                logging.critical(
                    f'Could not set necessary port stream of {port_stream} of sub components to port {port.get_stream_type()}'
                    f'of component {self.__class__.__name__}')

        if abs(abs(controlled_port.get_stream()) - abs(port_value)) > 1e-3:
            logging.critical(f'Port {controlled_port.get_id()} of Component {self.component_id} (Ely) does not have '
                             f'expected value if sub components are summed up.')
