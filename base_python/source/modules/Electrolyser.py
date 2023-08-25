#  imports
from base_python.source.modules.GenericUnit import GenericUnit
from base_python.source.basic import ModelSettings
from base_python.source.modules.Converter import Converter
from base_python.source.basic.Streamtypes import *
from base_python.source.basic.Units import Unit
from base_python.source.basic.Quantities import PhysicalQuantity
from base_python.source.model_base.Port_Mass import Port_Mass
from base_python.source.helper._FunctionDef import range_limit
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import GenericTechnicalInput
import logging
from scipy import interpolate
import numpy as np
import math
from enum import Enum, auto
from enum import Enum, auto
from base_python.source.helper import polarisation_curve_to_efficiency
from base_python.source.helper.Conversion import Time_Conversion


class Electrolyser(Converter):
    class Technology(StrEnum):
        PEM = auto()
        ALKALY = auto()
        SOEC = auto()

    def __init__(self, size=None, technology=Technology.PEM,
                 active=False, new_investment=False,
                 economical_parameters=None,
                 generic_technical_input: GenericTechnicalInput = None):
        """

        :param size: (float)            installed nominal Power, should be in kW
        :param technology: (Enum)       type of installation
        :param active: (bool)           true if the component controls the system
        :param new_investment:          true if CAPEX shall be included in balance
        :param economical_parameters:   see model_base/dataclasses for more info
        :param generic_technical_input: see model_base/dataclasses for more info
        """

        super().__init__(size=size, technology=technology, active=active,
                         new_investment=new_investment, economical_parameters=economical_parameters,
                         generic_technical_input=generic_technical_input)  # initialize class generic unit
        # set inherited variables
        self.size = size

        self.possible_streams = {}

        # inputs
        super()._add_port(port_type=StreamEnergy.ELECTRIC,
                          component_ID=self.component_id,
                          fixed_status=True,
                          sign=StreamDirection.stream_into_component,
                          unit=Unit.kW)  # [kW]
        super()._add_port(port_type=StreamMass.WATER,
                          component_ID=self.component_id,
                          fixed_status=True,
                          sign=StreamDirection.stream_into_component,
                          unit=Unit.kg)  # [kg]

        # outputs
        super()._add_port(port_type=StreamMass.HYDROGEN,
                          component_ID=self.component_id,
                          fixed_status=True,
                          sign=StreamDirection.stream_out_of_component,
                          unit=Unit.kg)  # [kg]
        super()._add_port(port_type=StreamMass.OXYGEN,
                          component_ID=self.component_id,
                          fixed_status=True,
                          sign=StreamDirection.stream_out_of_component,
                          unit=Unit.kg)  # [kg]
        if self.technology == 'SOEC':
            super()._add_port(port_type=StreamEnergy.HEAT,
                              component_ID=self.component_id,
                              fixed_status=True,
                              sign=StreamDirection.stream_into_component,
                              unit=Unit.kW)  # [kW]
        else:
            super()._add_port(port_type=StreamEnergy.HEAT,
                              component_ID=self.component_id,
                              fixed_status=True,
                              sign=StreamDirection.stream_out_of_component,
                              unit=Unit.kW)  # [kW]

        # initial controll port is electrical port
        self.controlled_port = self.get_ports_by_type_and_sign(StreamEnergy.ELECTRIC,
                                                               StreamDirection.stream_into_component)

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

        if not self.active:
            self._set_adaptive_port(self.controlled_port.get_type(), self.controlled_port.get_sign())
        else:
            self._set_fixed_port(self.controlled_port.get_type(), self.controlled_port.get_sign())

        electrical_efficiency_kg_per_kWh_HHV = self._get_efficiency(medium_referenced=StreamEnergy.ELECTRIC,
                                                                    medium_calculated=StreamMass.HYDROGEN)  # kWh --> m³

        self.value_calculation = {
            # TODO: Umrechnungsfaktoren der Helper-Fkt für diese Berchnung nutzen
            (StreamEnergy.ELECTRIC, StreamTypes.power): lambda load:
            -load / 100 if electrical_efficiency_kg_per_kWh_HHV(load).min() != 0 else 0,
            # kW = kg/(kg/m³) * (60 min/h)/min * kWh/m³

            (StreamEnergy.HEAT, StreamTypes.power): lambda load:
            -(self.value_calculation[(StreamEnergy.ELECTRIC, StreamTypes.power)](load) -
              (self.value_calculation[(StreamMass.HYDROGEN, StreamTypes.mass)](load) *
               ModelSettings.stream_types[StreamMass.HYDROGEN][PhysicalQuantity.higher_heating_value] *
               60 / self.time_resolution)),
            # kW = kW - (kg * kWh/kg *(60min/h)/min)

            (StreamMass.HYDROGEN, StreamTypes.mass): lambda load:
            -self.value_calculation[(StreamEnergy.ELECTRIC, StreamTypes.power)](
                load) * electrical_efficiency_kg_per_kWh_HHV(load).min() *
            Time_Conversion.hour2resolution(self.time_resolution),
            # kg/kW = [-] /(60min/h)*(min) / (kWh/m³) * (kg/m³)

            (StreamMass.OXYGEN, StreamTypes.mass): lambda load:
            0.5 * ModelSettings.stream_types[StreamMass.OXYGEN][PhysicalQuantity.molar_mass] /
            ModelSettings.stream_types[StreamMass.HYDROGEN][PhysicalQuantity.molar_mass] *
            self.value_calculation[(StreamMass.HYDROGEN, StreamTypes.mass)](load),
            # kg/kW = (kg/mol) / (kg/mol) * kg

            (StreamMass.WATER, StreamTypes.mass): lambda load:
            -(self.value_calculation[(StreamMass.HYDROGEN, StreamTypes.mass)](load) +
              self.value_calculation[(StreamMass.OXYGEN, StreamTypes.mass)](load))
            # kg/kW = kg + kg
        }

        self._set_possible_streams(load_range=electrical_efficiency_kg_per_kWh_HHV.x)


if __name__ == '__main__':
    print('T E S T: Electrolyser')

    My_Plant = Electrolyser(size=2000, technology=Electrolyser.Technology.PEM)
    My_Plant.run()
