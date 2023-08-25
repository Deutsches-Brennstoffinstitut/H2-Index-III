from base_python.source.basic.Quantities import *
from base_python.source.basic.Streamtypes import *
from base_python.source.basic.Units import Unit

from base_python.source.model_base.Port import Port
from base_python.source.basic import ModelSettings
from base_python.source.helper import RefPropFluid
import os.path
import math
import sys

from base_python.source.basic.Streamtypes import StreamDirection
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import CoolProp.CoolProp as CoolProp
from CoolProp import AbstractState
from base_python.source.basic.CustomErrors import PortMassError
root = os.environ['RPPREFIX']
R = REFPROPFunctionLibrary(root)
R.SETPATHdll(root)


class Port_Mass(Port):
    stream_types = {}

    def __init__(self, component_ID:str,port_id: str, port_type: StreamMass = None, external_identifier=None,
                 sign: StreamDirection = StreamDirection.stream_bidirectional, unit: Unit = None,
                 fixed_status: bool = False, pressure: float = math.inf,
                 temperature: float = math.inf):
        """
        Args:
            port_id (str):          Id of the port
            port_type (StreamMass): Type of the port (e.g. H2, CO2)
            sign (int):             Sign of the port which defines the possible flow direction of the port based on
                                    the general conventions
            unit (Unit):            Unit of the ports stream
            fixed_status (bool):    Defines whether the port is a fixed one or not based on general conventions
            pressure (float):       Pressure value of the port
            temperature (float):    Temperature value of the port
        """
        super().__init__(component_ID=component_ID, port_id=port_id, sign=sign, unit=unit, fixed_status=fixed_status, external_identifier=None)

        self.temperature = None
        self.pressure = None
        self.updated_fluid = 1
        self.value_profiles = {}
        self.mass_fraction = {}

        self.set_type_and_unit(port_type, unit)
        self.port_properties = self._create_fluid()
        try:
            self.port_properties_norm = RefPropFluid.create_fluid(self.mass_fraction, temperature=293.15,
                                                                  pressure=101325)
        except:
            logging.warning(f'Could not create norm properties of port {self.port_results.port_id} of type {self.port_results.port_type}')

        self.property_status = {PhysicalQuantity.pressure: 1, PhysicalQuantity.temperature: 1,
                                PhysicalQuantity.mass_fraction: 1, PhysicalQuantity.mass_stream: 1}

        self.set_pressure(pressure)
        self.set_temperature(temperature)
        self.port_results.port_history.setdefault(PhysicalQuantity.mass_fraction, [])
        self.port_results.port_history.setdefault(PhysicalQuantity.pressure, [])
        self.port_results.port_history.setdefault(PhysicalQuantity.temperature, [])
        self.port_results.port_history.setdefault(PhysicalQuantity.stream, [])

    def reset_history(self):

        super().reset_history()
        self.property_status = {PhysicalQuantity.pressure: 1, PhysicalQuantity.temperature: 1,
                                PhysicalQuantity.mass_fraction: 1, PhysicalQuantity.mass_stream: 1}

        self.port_results.port_history.setdefault(PhysicalQuantity.mass_fraction, [])
        self.port_results.port_history.setdefault(PhysicalQuantity.pressure, [])
        self.port_results.port_history.setdefault(PhysicalQuantity.temperature, [])
        self.port_results.port_history.setdefault(PhysicalQuantity.stream, [])

    def set_type_and_unit(self, port_type: StreamMass, unit: Unit):
        """
        This method sets the type of the port and based on this also the mass fraction, unit and the stream_type

        Args:
            port_type (StreamMass): Type of the port (e.g. StreamMass.HYDROGEN, StreamMass.OXYGEN)
            unit (Unit):            Unit of the stream for this port (e.g. Unit.kg)

        """
        if unit != get_stream_unit(port_type) and unit is not None:
            logging.critical(f'Given stream unit {unit} of type {port_type.value} does not match model convention')
        else:
            if self.port_results.port_type is None:
                self.port_results.port_type = port_type
                if sum(ModelSettings.stream_types[port_type][PhysicalQuantity.mass_fraction].values()) != 1:
                    raise PortMassError(f'Mass Fraction of Port {self.port_results.port_id} type: {self.port_results.port_type} != 1')

                self.mass_fraction.update(ModelSettings.stream_types[port_type][PhysicalQuantity.mass_fraction])
                self.stream_type = get_stream_type(port_type)
                self.port_results.stream_unit = unit
            else:
                logging.warning(f'Trying to change Port Type of port {self.port_results.port_id}')

    def set_status_calculated(self):
        """
        This method is used to set the property status of all properties to calculated (1) for this timestep. It has to
        be reset to uncalculated if new port porperties are set.

        """
        self.property_status = dict.fromkeys(self.property_status, 1)

    def set_status_uncalculated(self):
        """
        Sets the calculation status of the port to not calculated (0) So if properties of the port change it will
        perform a calculation of the refprop properties

        """
        self.property_status = dict.fromkeys(self.property_status, 0)

    def set_pressure(self, pressure: float):
        """

        Args:
            pressure (float): New pressure value of the port given in Pa

        """
        self.pressure = pressure
        self.property_status[PhysicalQuantity.pressure] = 0
        self.updated_fluid = 1

    def set_temperature(self, temperature: float):
        """

        Args:
            temperature (float): New temperature value of the port given in K

        """
        self.temperature = temperature
        self.property_status[PhysicalQuantity.temperature] = 0
        self.updated_fluid = 1

    def set_mass_fraction(self, mass_fractions: dict):
        """

        Args:
            mass_fractions (dict): Dictionary of the molecule types as keys and their mass_fractions as values

        """
        self.property_status[PhysicalQuantity.temperature] = 0
        self.mass_fraction.update(mass_fractions)
        self.updated_fluid = 1

    def set_all_properties(self, runcount: int, port: Port):
        """
        Duplicates all properties of another port to this port. This function is useful if a component has two
        ports which always have the same properties.

        Args:
            port (object): Port which contains the information that shall be used for this port
            runcount (int): The actual runcount for which the stream parameter shall be set, to perform a comparison
                            with a possibly given profile
        """

        self.set_pressure(port.get_pressure())
        self.set_temperature(port.get_temperature())
        self.set_stream(runcount, port.get_stream())
        self.set_mass_fraction(port.get_mass_fraction())

    def get_molar_mass(self) -> float:
        """

        Returns:
            float: Molar Mass of the actual port with the given mass fractions
        """
        return self.port_properties.molar_mass()

    def get_norm_density(self) -> float:
        """

        Returns:
            float: Densitiy of the port with given mass_fraction at norm conditions
        """
        return self.port_properties_norm.rhomass()

    def get_density(self) -> float:
        """

        Returns:
            float: Density of the ports stream
        """
        if self.updated_fluid != 0:
            self._update_fluid()
        return self.port_properties.rhomass()

    def get_pressure(self) -> float:
        """

        Returns:
            float: Pressure of the ports stream
        """
        return self.pressure

    def get_pressure_status(self) -> int:

        """

        Returns:
            float: Status of the pressure variable (0 = uncalculated, 1 = calculated)
        """

        return self.property_status[PhysicalQuantity.pressure]

    def get_temperature(self) -> float:
        """

        Returns:
            float: Temperature of the ports stream
        """
        return self.temperature

    def get_temperature_status(self) -> int:
        """

        Returns:
            float: Status of the temperature variable (0 = uncalculated, 1 = calculated)
        """

        return self.property_status[PhysicalQuantity.temperature]

    def get_mass_fraction(self) -> dict:
        """

        Returns:
            dict: Mass fraction the ports stream with molecule types as keys and mass fractions as values
        """
        return self.mass_fraction

    def get_mass_fraction_status(self) -> int:
        """

        Returns:
            float: Status of the mass_fraction variable (0 = uncalculated, 1 = calculated)
        """
        return self.property_status[PhysicalQuantity.mass_fraction]

    def get_all_properties(self) -> dict:
        """
        Returns:
            dict: All properties which describe the actual state of the port
        """

        resulting_dictionary = {}
        resulting_dictionary[PhysicalQuantity.pressure] = self.get_pressure()
        resulting_dictionary[PhysicalQuantity.temperature] = self.get_temperature()
        resulting_dictionary[PhysicalQuantity.mass_fraction] = self.get_mass_fraction()
        resulting_dictionary[PhysicalQuantity.stream] = self.get_stream()
        return resulting_dictionary

    def save_state(self):
        """
        Safes the actual values of the port in value history so it is possible to read the history later

        """
        super().save_state()
        self.port_results.port_history[PhysicalQuantity.mass_fraction].append(self.mass_fraction)
        self.port_results.port_history[PhysicalQuantity.pressure].append(self.pressure)
        self.port_results.port_history[PhysicalQuantity.temperature].append(self.temperature)
        self.port_results.port_history[PhysicalQuantity.stream].append(self.stream)

    def _update_fluid(self):
        """
        Updates the ports properties when fraction, temperature or pressure changed

        """
        if (self.temperature is not None) and (self.pressure is not None) and (self.mass_fraction != {}):
            self.port_properties.set_mass_fractions(list(self.mass_fraction.values()))
            self.port_properties.update(CoolProp.PT_INPUTS, self.pressure, self.temperature)
            self.updated_fluid = 0

    def _create_fluid(self) -> RefPropFluid:
        """
        Creates the Refprop fluid using the saved properties in the stream

        """
        components_string = ""
        fractions = []
        if self.mass_fraction != {}:
            components_string = '&'.join([key.name for key in self.mass_fraction.keys()])
            fractions = list(self.mass_fraction.values())
        else:
            logging.warning(f'No mass fraction given for Port {self.port_results.port_id} of type {self.port_results.port_type}')
        my_abstract_state = AbstractState("REFPROP", components_string)
        my_abstract_state.set_mole_fractions(fractions)
        return my_abstract_state
