#  imports
from base_python.source.modules.GenericUnit import GenericUnit
import random
from base_python.source.model_base.Port_Mass import Port_Mass
from base_python.source.basic import ModelSettings
from base_python.source.helper import RefPropFluid
from base_python.source.basic import Database
import math
from ctREFPROP.ctREFPROP import REFPROPFunctionLibrary
import CoolProp.CoolProp as CoolProp
from CoolProp.CoolProp import PropsSI
from CoolProp import AbstractState
from enum import Enum, auto
from base_python.source.basic.Streamtypes import StreamEnergy, StreamMass, StreamDirection
from base_python.source.basic.Units import Unit
from base_python.source.basic.Quantities import PhysicalQuantity
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import GenericTechnicalInput

import logging


class Compressor(GenericUnit):
    class Technology(Enum):
        PISTON = auto()
        TURBO = auto()

    def __init__(self, size=None, technology=None, active=False, stream_type=None, max_stream=None,
                 new_investment=False,
                 compression_efficiencies={'mechanical': 0.9, 'isentropic': 0.72, 'electrical': 0.98},
                 economical_parameters=None, stages=1, cooling_temperature=3000, pressure_out=None,
                 generic_technical_input: GenericTechnicalInput = None):

        """

        Init method of component compressor which initializes the compressor as primary component or sub component
        Notes: 13.12.2022 FFi: size und max_stream sind zwei verschiedene sachen. max_stream legt die limits fest und
        size macht prinzipiell das gleiche aber legt keine limits fest. da size =None kann man einen Compressor
        initialisieren der nie funktionieren wird, weil irgendwo dann self.stream < self.size oder so steht und ein
        integer mit None verglichen wird was einen TypeError auswirft -> size darf sogesehen nie None sein Args: size
        (float): Electrical size of the compressor in kW technology (Enum): Technology of compressor which could have
        influence on the investment costs stream_type (Enum): The stream_type and the port sign of the port which is
        used to control the component active (bool): Describes whether the component is active or passive. Has
        influence on how the component is run new_investment (bool): Determines whether its a new investment so the
        annuity is calculated or not investment_costs (float): Contains the specific costs of the component. If not
        given values from database are taken in € stages (int): Number of compression stages for calculation
        cooling_temperature (float): Temperature which has to be reached by cooling after every step in K
        pressure_out (float): Pressure of the output stream can be set fix here if necessary in Pa

        """
        if size == None:
            raise ValueError("Size of Compressor is 'None'! Give the compressor a size!")
        super().__init__(size=size, technology=technology, active=active,
                         new_investment=new_investment, economical_parameters=economical_parameters,
                         stream_type=stream_type, generic_technical_input=generic_technical_input)
        self.pressure_out_init = pressure_out
        self.pressure_in = None
        self.temperature_in = None
        self.pressure_out = None
        self.temperature_out = None
        self.compression_efficiencies = compression_efficiencies
        self.number_stages = stages
        self.specific_gas_constant = None
        self.molar_mass = None
        self.pressure_critical = None
        self.temperature_critical = None
        self.isentropic_exponent = None
        self.stream_limit = max_stream  # TODO: Hier ist unter Umständen eine Umrechnung anhand der Time-resolution notwendig
        self.temporary_fluids = {}
        self.cooling_temperature = cooling_temperature
        self.mass_fraction = {}
        self.mass_ports = {}

    def set_properties(self):
        """
        Sets the basic properties of the component as the necessary ports for calculation and gas parameters

        """

        if self.stream_type not in StreamEnergy:
            self.mass_ports['in'] = self._add_port(port_type=self.stream_type,
                                                   component_ID=self.component_id,
                                                   fixed_status=self.active,
                                                   sign=StreamDirection.stream_into_component)
            self.mass_ports['out'] = self._add_port(port_type=self.stream_type,
                                                    component_ID=self.component_id,
                                                    fixed_status=True,
                                                    sign=StreamDirection.stream_out_of_component)
            if self.stream_limit is not None:
                self.mass_ports['in'].set_stream_limit((-self.stream_limit, self.stream_limit))

        super()._add_port(port_type=StreamEnergy.ELECTRIC,
                          component_ID=self.component_id,
                          fixed_status=True,
                          sign=StreamDirection.stream_into_component,
                          unit=Unit.kW)
        if self.mass_fraction != {}:
            self._update_mass_fraction(self.mass_fraction)

    def _update_mass_fraction(self, mass_fraction):
        """
        This method updates the mass fraction of the component. Therefore the run method checks whether mass_fraction changes.
        If the mass fraction changes gas parameters have to be recalculated

        Args:
            mass_fraction (dict): Dictionary of components and their fractions

        """

        self.mass_fraction.update(mass_fraction)
        self.compression_fluid_norm = RefPropFluid.create_fluid(mass_fraction, temperature=273.15, pressure=101325)
        self._set_gas_parameters_for_calculation()

    def _set_gas_parameters_for_calculation(self):
        """
        This function sets the gas parameters which are indipendent from pressure and temperature and only have to be calculated once

        """

        self.specific_gas_constant = self._get_specific_gas_constant()
        self.temperature_critical = self.compression_fluid_norm.T_critical()
        self.pressure_critical = self.compression_fluid_norm.p_critical()

    def _get_specific_gas_constant(self):
        """
        Method to get the specific gas constant from RefProp

        Returns:
            float: Specific gas constant of the fluid
        """

        fluid = self.compression_fluid_norm
        return Database.general_gas_constant / fluid.molar_mass()

    def _get_real_gas_factor(self, pressure, temperature):
        """
        Method to get the real gas factor from RefProp

        Args:
            pressure (float): Pressure of the fluid in Pa
            temperature (float): Temperature of the fluid in K

        Returns:
            float: Real gas factor of the fluid
        """

        fluid = self._get_compression_fluid(pressure, temperature)
        z = fluid.compressibility_factor() / self.compression_fluid_norm.compressibility_factor()
        return z

    def _get_isentropic_exponent(self, pressure, temperature):
        """
        Method to get the isentropic exponent from RefProp

        Args:
            pressure (float): Pressure of the fluid in Pa
            temperature (float): Temperature of the fluid in K

        Returns:
            float: Isentropic exponent of the fluid
        """
        fluid = self._get_compression_fluid(pressure, temperature)
        return fluid.cpmass() / fluid.cvmass()

    def _get_specific_heat_capacity(self, pressure, temperature):
        """
        Method to get the specific heat capacity from RefProp

        Args:
            pressure (float): Pressure of the fluid in Pa
            temperature (float): Temperature of the fluid in K

        Returns:
            float: Specific heat capacity of the fluid
        """
        fluid = self._get_compression_fluid(pressure, temperature)
        return fluid.cpmass()

    def _get_compression_fluid(self, pressure, temperature):
        """
        Necessary method to get all properties for the right thermodynamical state. If the state already has been calculated its returned by the hash

        Args:
            pressure (float): Pressure of the fluid in Pa
            temperature (float): Temperature of the fluid in K

        Returns:
            object: The fluid state to get the necessary parameters
        """

        key = hash(
            tuple(list(self.mass_fraction.keys()) + list(self.mass_fraction.values()) + [pressure] + [temperature]))
        fluid = self.temporary_fluids.get(key)
        if fluid is None:
            fluid = RefPropFluid.create_fluid(self.mass_fraction, pressure=pressure, temperature=temperature)
            self.temporary_fluids[key] = fluid
        return fluid

    def check_kwargs(self, kwargs):
        """
        This method checks whether there are additional arguments in the run method which is used if the compressor
        is used as a sub component of another component (e.g. gas storage)

        Args:
            kwargs (dict): Dictionary of keywords and values given to the run method

        """

        if self.pressure_in == None or abs(self.pressure_in) == math.inf:
            if 'pressure_in' in kwargs:
                self.pressure_in = kwargs.get('pressure_in')
        if self.pressure_out == None or abs(self.pressure_out) == math.inf:
            if 'pressure_out' in kwargs:
                self.pressure_out = kwargs.get('pressure_out')
            elif self.pressure_out_init != None:
                self.pressure_out = self.pressure_out_init
        if self.temperature_in == None or abs(self.temperature_in) == math.inf:
            if 'temperature_in' in kwargs:
                self.temperature_in = kwargs.get('temperature_in')
        if self.temperature_out == None or abs(self.temperature_out) == math.inf:
            if 'temperature_out' in kwargs:
                self.temperature_out = kwargs.get('temperature_out')

    def run(self, port, branch_information, runcount=0, **kwargs):
        """
        The main run method of the compressor

        Args:
            port_id (str): Id of the port which is connected to the actual calculated branch
            branch_information (dict): Actual information about the branch status (temperature, pressure, stream, fraction)
            runcount (int): The actual calculated step of the model
            **kwargs (dict): Additional arguments which can be used to calculate the Compressor as sub component (pressure_in, temperature_in, pressure_out, temperature_out)

        """

        self.pressure_in = None
        self.temperature_in = None
        self.pressure_out = None
        self.temperature_out = None

        if branch_information[PhysicalQuantity.mass_fraction] != self.mass_fraction:
            self._update_mass_fraction(branch_information[PhysicalQuantity.mass_fraction])

        branch_connected_port = self.get_port_by_id(port) if isinstance(port, str) else port
        port_mass_in = self.mass_ports['in']
        port_mass_out = self.mass_ports['out']

        self.stream = branch_information[PhysicalQuantity.stream]
        self.mass_fraction = branch_information[PhysicalQuantity.mass_fraction]
        if branch_connected_port == port_mass_in:
            self.pressure_in = branch_information[PhysicalQuantity.pressure]
            self.temperature_in = branch_information[PhysicalQuantity.temperature]
        elif branch_connected_port == port_mass_out:
            self.pressure_out = branch_information[PhysicalQuantity.pressure]
            self.temperature_out = branch_information[PhysicalQuantity.temperature]

        # Check whether run method contains additional values used if component is used as sub_component

        self.check_kwargs(kwargs)

        # Prepare the calculation media:

        port_mass_in.set_pressure(self.pressure_in)
        port_mass_out.set_pressure(self.pressure_out)
        port_mass_in.set_temperature(self.temperature_in)
        port_mass_out.set_temperature(self.temperature_out)
        port_mass_in.set_mass_fraction(self.mass_fraction)
        port_mass_out.set_mass_fraction(self.mass_fraction)
        port_mass_in.set_stream(runcount, self.stream)
        port_mass_out.set_stream(runcount, -self.stream)

        # check whether definition ok:

        if all([self.pressure_in is not None, self.pressure_out is not None, self.temperature_in is not None]):
            compression_parameters = self._calculate_compression_power(mass_flow=abs(port_mass_in.get_stream()),
                                                                       temperature_in=port_mass_in.get_temperature(),
                                                                       pressure_in=port_mass_in.get_pressure(),
                                                                       pressure_out=port_mass_out.get_pressure())
        else:
            logging.critical('Compressor insufficent defined to calculate compression power!')

        electric_port = self.get_ports_by_type_and_sign(StreamEnergy.ELECTRIC, StreamDirection.stream_into_component)

        if abs(compression_parameters[0]) > abs(self.size):
            logging.warning(f'Electrical Size of compressor insufficent at runcount {runcount}.')

        electric_port.set_stream(runcount, -compression_parameters[0])
        port_mass_out.set_temperature(self.temperature_out)

    def _calculate_compression_power(self, mass_flow, temperature_in, pressure_in, pressure_out):
        """
        Method to calculate the necessary compression power to compress the gas to the desired thermodynamical state

        Args:
            mass_flow (flaot): Mass flow in kg/time_resolution
            pressure_in (float): Inlet pressure of the compression in Pa
            pressure_out (float): Outlet pressure of the compression in Pa

        Returns:
            tuple: Tuple of (compression_power, cooling power)
        """

        # mass_flow = mass_flow / (self.time_resolution * 60)  # Calculate mass flow per second
        total_compression_ratio = pressure_out / pressure_in
        stage_compression_ratio = total_compression_ratio ** (1 / self.number_stages)
        stage_compression_power = []
        stage_temperatures_out = []
        stage_cooling_power = []
        stage_pressure_out = pressure_in
        stage_temperature_out = temperature_in
        for stage in range(self.number_stages):
            stage_pressure_in = stage_pressure_out
            stage_temperature_in = stage_temperature_out
            isentropic_exponent_in = self._get_isentropic_exponent(stage_pressure_in, stage_temperature_in)
            real_gas_factor_in = self._get_real_gas_factor(pressure=stage_pressure_in,
                                                           temperature=stage_temperature_in)  # Calculation with ideal gas

            stage_compression_power.append(
                self._calculate_stage_compression_power(isentropic_exponent_in, temperature_in,
                                                        self.specific_gas_constant, real_gas_factor_in, mass_flow,
                                                        stage_compression_ratio))
            stage_pressure_out = pressure_in * stage_compression_ratio
            stage_temperature_out = self._get_compression_temperature(temperature_in, isentropic_exponent_in,
                                                                      stage_compression_ratio)
            stage_cooling_power.append(
                self._calculate_stage_cooling_power(temperature_in, pressure_in * stage_compression_ratio, mass_flow))
            stage_temperatures_out.append(stage_temperature_out)
        compression_power = sum(stage_compression_power)
        cooling_power = sum(stage_cooling_power)
        if self.compression_efficiencies != None:
            for value in self.compression_efficiencies.values():
                if compression_power != 0:
                    compression_power /= value
                else:
                    break
        self.temperature_out = stage_temperatures_out[-1]
        return (compression_power, cooling_power)

    def _calculate_stage_compression_power(self, isentropic_exponent_mean, temperature_in, specific_gas_constant,
                                           real_gas_factor, mass_flow, compression_ratio):
        """
        Actual calculation method to get the compression power per compression stage

        Args:
            isentropic_exponent_mean (float): Isentropic exponent of the fluid at mean pressure and temperature
            temperature_in (float): Inlet temperature in K
            specific_gas_constant (flaot): Specific gas constant of the fluid
            compressibility_factor_mean (float): Compressibility factor of the fluid
            mass_flow (float): Mass flow in kg/time_resolution
            compression_ratio (float): Compression ratio of the calculated compression stage (p2/p1)

        Returns:
            float: Necessary stage compression power in kW
        """
        compression_work = (isentropic_exponent_mean / (isentropic_exponent_mean - 1)) * temperature_in * \
                           specific_gas_constant * real_gas_factor * \
                           (compression_ratio ** (
                                   (isentropic_exponent_mean - 1) / isentropic_exponent_mean) - 1)  # J/kg
        compression_power = compression_work * mass_flow  # J/time_resolution min
        compression_power = compression_power / (self.time_resolution * 60) / 1000  # J/s = W W/1000 = kW
        return compression_power

    def _get_compression_temperature(self, temperature_in, isentropic_exponent, compression_ratio):
        """
        Method to calculate the outlet temperature after stage compression

        Args:
            temperature_in (float): Inlet temperature of the calculated stage in K
            isentropic_exponent (float): Isentropic exponent of the calculated fluid
            compression_ratio (float): Compression ratio of the calculated compression stage (p2/p1)

        Returns:
            float: Outlet temperature of the calculated compression stage in K
        """

        return ((temperature_in) * compression_ratio ** ((isentropic_exponent - 1) / isentropic_exponent))

    def _calculate_stage_cooling_power(self, temperature_in, pressure, mass_flow):
        """
        Method to calculate
        Args:
            temperature_in (float): Inlet temperature of the calculated stage in K
            pressure (float): Pressure after compression in Pa
            mass_flow (float): Mass flow in kg/time_resolution

        Returns:
            float: Neccessary cooling power in kW
        """
        if self.cooling_temperature < temperature_in:
            temperature_mean = temperature_in - (temperature_in - self.cooling_temperature) / 2
            specific_heat_capacity = self._get_specific_heat_capacity(pressure, temperature_mean)
            cooling_power = specific_heat_capacity * mass_flow * (self.cooling_temperature - temperature_in)
            return cooling_power / 3600 / 1000  # Unit transformation from kJ to W to kW
        else:
            return 0

    # def _get_mean_temperature_pressure(self, compression_ratio, temperature_in, pressure_in):
    #     isentropic_exponent_in = self._get_isentropic_exponent(pressure=pressure_in, temperature=temperature_in)
    #     temperature_out_predicted = self._get_compression_temperature(temperature_in, isentropic_exponent_in,
    #                                                                   compression_ratio)
    #     temperature_mean = temperature_in + (temperature_out_predicted - temperature_in) / 2
    #     return temperature_mean
