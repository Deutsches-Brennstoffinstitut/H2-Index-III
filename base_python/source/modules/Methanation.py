#  imports
import logging
from base_python.source.basic import ModelSettings
from base_python.source.modules.GenericUnit import GenericUnit
from base_python.source.modules.Converter import Converter
import base_python.source.basic.ModelSettings as Settings
# from base.source.helper._FunctionDef import range_limit
from base_python.source.basic.Streamtypes import StreamEnergy, StreamMass, StreamDirection, StreamTypes
from base_python.source.basic.Units import Unit
from base_python.source.basic.Quantities import PhysicalQuantity
from scipy import interpolate
import numpy as np
import math
from base_python.source.basic.Streamtypes import StreamDirection
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import GenericTechnicalInput

from enum import Enum, auto


class Methanation(Converter):
    class Technology(Enum):
        H2 = auto()
        CH4 = auto()

    def __init__(self, size=None, technology=None, active=False, new_investment=False,
                 economical_parameters=None, generic_technical_input: GenericTechnicalInput = None):
        """
        :param size:         installed nominal Power, should be in kW
        :param technology:   type of installation ('PEM', 'Alkaly', 'HT',....)
        :param controlled_medium: select the controlling port {'electric', 'O2', 'H2', 'H2O', 'heat'}
        :param active:       define whether the component controls the system
        :param efficiency:   net efficiency for the charge and discharge process
        """
        super().__init__(size=size, technology=technology, active=active,
                         new_investment=new_investment,
                         economical_parameters=economical_parameters,
                         generic_technical_input=generic_technical_input)  # initialize class generic unit
        # set inherited variables
        self.size = size
        self.possible_streams = {}
        # inputs
        if self.technology == self.Technology.H2:
            self.energy_carrier = StreamMass.HYDROGEN
            super()._add_port(port_type=StreamMass.HYDROGEN,
                              component_ID=self.component_id,
                              fixed_status=True,
                              sign=StreamDirection.stream_into_component,
                              unit=Unit.kg)  # [kg]

        if self.technology == self.Technology.CH4:
            self.energy_carrier = StreamMass.NG_RUSSIA_H
            super()._add_port(port_type=StreamMass.NG_RUSSIA_H,
                              component_ID=self.component_id,
                              fixed_status=True,
                              sign=StreamDirection.stream_into_component,
                              unit=Unit.kg)  # [kg]
        # outputs

        super()._add_port(port_type=StreamEnergy.HEAT,
                          component_ID=self.component_id,
                          fixed_status=True,
                          sign=StreamDirection.stream_out_of_component,
                          unit=Unit.kW)
        super()._add_port(port_type=StreamEnergy.ELECTRIC,
                          component_ID=self.component_id,
                          fixed_status=True,
                          sign=StreamDirection.stream_out_of_component,
                          unit=Unit.kW)
        super()._add_port(port_type=StreamMass.CO2,
                          component_ID=self.component_id,
                          fixed_status=True,
                          sign=StreamDirection.stream_out_of_component,
                          unit=Unit.kg)

    #############################
    # Module specific functions #
    ############################

    def set_properties(self):
        """
        Calculate object specific properties from KPI
        has to be called
        - after model definition (after set_KPI_to_components())
        - after setting of time_resolution in the model
        from model class
        :return: self
        """

        if self.active == False:
            if self.controlled_port != None:
                self._set_adaptive_port(self.controlled_port.get_type(), self.controlled_port.get_sign())
            else:
                self._set_adaptive_port(StreamEnergy.ELECTRIC, StreamDirection.stream_into_component)
        else:
            if self.controlled_port != None:
                self._set_fixed_port(self.controlled_port.get_type(), self.controlled_port.get_sign())
            else:
                self._set_fixed_port(StreamEnergy.ELECTRIC, StreamDirection.stream_into_component)

        self.interpolation_functions = {}
        self.port_limits = {}

        # Absolute calculation rules of input/output streams

        # TODO: Bei den possible streams wird noch keine Überprüfung der Einheiten durchgeführt, dementsprechend gibt es keine überpürfung ob die Einheiten, die bei den Wirkungsgraden übergeben werden passen

        # TODO: get_efficiency_at_reference_load
        self.value_calculation = {
            (self.energy_carrier, StreamTypes.mass):
                lambda load: self.size / 60 * self.time_resolution / self.get_efficiency_at_reference_load(
                    StreamEnergy.ELECTRIC, load) /
                             ModelSettings.stream_types[self.energy_carrier][PhysicalQuantity.higher_heating_value]
                if self.get_efficiency_at_reference_load(StreamEnergy.ELECTRIC, load) != 0 else 0,
            # kg = kW /(60 min/h) * min / (kWh/kWh) / (kWh/kg)
            (StreamEnergy.ELECTRIC, StreamTypes.power):
                lambda load: self.value_calculation[(self.energy_carrier, StreamTypes.mass)](load) *
                             self.get_efficiency_at_reference_load(StreamEnergy.ELECTRIC, load) *
                             ModelSettings.stream_types[self.energy_carrier][
                                 PhysicalQuantity.higher_heating_value] * 60 /
                             self.time_resolution,
            # kW = kg * (kWh/kWh) * (kWh/kg) * 60 (min/h) / min
            (StreamEnergy.HEAT, StreamTypes.power):
                lambda load: self.value_calculation[(StreamEnergy.ELECTRIC, StreamTypes.power)](load) /
                             self.get_efficiency_at_reference_load(StreamEnergy.ELECTRIC, load) *
                             self.get_efficiency_at_reference_load(StreamEnergy.HEAT, load) if
                self.get_efficiency_at_reference_load(StreamEnergy.ELECTRIC, load) != 0 else 0,
            # kW = kW /(kWh/kWh) * (kWh/kWh)
            (StreamMass.CO2, StreamTypes.mass):
                lambda load: self.value_calculation[(self.energy_carrier, StreamTypes.mass)](load) *
                             ModelSettings.stream_types[self.energy_carrier][PhysicalQuantity.higher_heating_value] *
                             self.get_efficiency_at_reference_load(StreamMass.CO2, load)
            # kg = kg * (kWh/kg) * (kg/kWh)
        }
        #todo: loadrange auslesen und der funktion set_possible streams übergeben
        self._set_possible_streams()
