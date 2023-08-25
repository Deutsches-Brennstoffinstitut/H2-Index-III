from base_python.source.modules.Storage import Storage
from base_python.source.modules.Compressor import Compressor
from base_python.source.helper._FunctionDef import range_limit
from base_python.source.helper._FunctionDef import in_range
from base_python.source.basic.Streamtypes import StreamEnergy, StreamMass
from base_python.source.basic.Units import Unit
from base_python.source.basic.Quantities import PhysicalQuantity
import base_python.source.basic.Database as Constants
from scipy.optimize import newton
from base_python.source.helper import RefPropFluid
from base_python.source.basic.Streamtypes import StreamDirection
import base_python.source.basic.ModelSettings as Settings
from base_python.source.model_base.Port_Energy import Port_Energy
import logging
import math
from enum import Enum, auto
from base_python.source.model_base.Dataclasses.TechnicalDataclasses import GenericTechnicalInput


class Storage_Gas(Storage):
    class Technology(Enum):
        CAVERN = auto()
        TANK_U100BAR = auto()

    def __init__(self, stream_type: StreamMass, size: float = None, technology=None, pressure_min=None,
                 pressure_max=None,
                 storage_temperature=283.15, cushion_gas_volume=0, storage_volume=0,
                 active=False, initial_value=None, efficiency: float = 1.0,
                 new_investment=False, economical_parameters=None, include_compression=False,
                 generic_technical_input: GenericTechnicalInput = None
                 ):

        """
        Todo:
            Internal mass fraction not taken into account. For now the mass fraction is always set to the input mass fraction
            Temperature equalization in cavern has to be considered
        Args:
            size (float): Maximum storage capacity in kg
            technology (Enum): Type of the storage ('cavern','tank')
            stream_type (Enum): Tuple of the stream type connected and the port which is controlled
            pressure_min (float): Minimum pressure in Pa
            pressure_max (float): Maximum pressure of the storage in Pa
            storage_temperature (float): Storage temperature in K
            cushion_gas_volume (float): Volume of the cushion gas in Nm³
            active (bool): Boolean whether the component is active or passive
            initial_value (float): Initial value of the storage in kg
            efficiency (float): Storage charge and discharge efficiency
            new_investment (bool): Boolean whether the storage is a new investment
            investment_costs (float): Absolute investment costs for the storage in €
            include_compression (bool): Boolean whether the compression of the storage is included in calculation
        """

        super().__init__(size=size, technology=technology, active=active, initial_value=initial_value,
                         efficiency=efficiency, new_investment=new_investment,
                         economical_parameters=economical_parameters, stream_type=stream_type,
                         generic_technical_input=generic_technical_input)

        self.include_compression = include_compression
        self.pressure_min = pressure_min
        self.pressure_max = pressure_max
        self.storage_temperature = storage_temperature
        self.storage_volume = storage_volume
        self.cushion_gas_volume = cushion_gas_volume
        self.van_der_waals_a = None
        self.van_der_waals_b = None
        self.buffer_min = None
        self.mass_fraction = {}
        self.mass_ports = {}
        self.component_technical_results.component_history[PhysicalQuantity.pressure] = []
        self.component_technical_results.component_history['storage_level'] = []
        self._add_port(port_type=self.stream_type,component_ID=self.component_id,
                       fixed_status=active, sign=StreamDirection.stream_into_component)
        self._add_port(port_type=self.stream_type, component_ID=self.component_id,
                       fixed_status=active, sign=StreamDirection.stream_out_of_component)

        if self.stream_type == None:
            logging.critical('Storage medium must be defined!')

        self.buffer_profile = []
        self.pressure_profile = []

        if technology is not None:
            self.technology = technology
        else:
            self.technology = Storage_Gas.Technology.TANK_U100BAR

    def set_properties(self):
        """
        Basic function to set main properties of the component

        """
        self.mass_ports['in'] = self.get_ports_by_type_and_sign(self.stream_type,
                                                                StreamDirection.stream_into_component)
        self.mass_ports['out'] = self.get_ports_by_type_and_sign(self.stream_type,
                                                                 StreamDirection.stream_out_of_component)

        self.gas_properties_norm = RefPropFluid.create_fluid(self.mass_ports['in'].get_mass_fraction(), pressure=101325,
                                                             temperature=273.15)
        self._set_van_der_waals()
        if self.size is not None and self.pressure_min is not None and self.pressure_max is not None:
            self._set_gas_volumes_from_size()
            self._set_cushion_gas_volume_from_storage_volume()
        elif self.cushion_gas_volume != 0:
            self._set_storage_volume_from_cushion_gas_volume()
        elif self.storage_volume != 0:
            self._set_cushion_gas_volume_from_storage_volume()

        if self.pressure_min is not None:
            self.buffer_min = self._get_mass_content_from_pressure(self.pressure_min)

        if self.size != None:
            if self.buffer_init > self.size: self.buffer_init = self.size
        elif self.buffer_init != None:
            if self.pressure_max is not None:
                self.size = self._get_mass_content_from_pressure(self.pressure_max) - self.buffer_min
                if self.buffer_init > self.size:
                    logging.warning(
                        f'Given initial buffer level of {self.buffer_init} is more than maximum storage capacity of {self.size} '
                        f'which is defined by pressure/volumen of the storage. Initial value is set to maximum of {self.size}')
                    self.buffer_init = self.size

        if self.include_compression:
            if str(Compressor.__name__) not in self.sub_components:
                logging.critical('No sub-class of type Compressor connected Storage_Gas. '
                                 'Define sub-class by set_sub_class(Compressor) or set include_compression '
                                 'attribute of Storage to false')
            else:
                self._add_port(port_type=StreamEnergy.ELECTRIC,
                               component_ID=self.component_id,
                               sign=StreamDirection.stream_into_component,
                               fixed_status=True)

    def _set_storage_volume_from_mass_content(self, mass_content):
        molar_content = self._get_molar_content_from_mass(mass_content)
        function = lambda volume: self._get_van_der_waals_pressure(molar_content, volume) - self.pressure_max
        self.storage_volume = newton(function, self._get_norm_volume(mass_content) * 1e5 / self.pressure_max)

    def _get_storage_volume_from_mass_content(self, mass_content):
        molar_content = self._get_molar_content_from_mass(mass_content)
        function = lambda volume: self._get_van_der_waals_pressure(molar_content, volume) - self.pressure_max
        storage_volume = newton(function, self._get_norm_volume(mass_content) * 1e5 / self.pressure_max)
        return storage_volume

    def _set_gas_volumes_from_size(self):

        function = lambda mass_content: (self._get_norm_volume(mass_content) -
                                         self._get_cushion_gas_volume_from_storage_volume(
                                             self._get_storage_volume_from_mass_content(mass_content))) - \
                                        self._get_norm_volume(self.size)
        mass_content_total = newton(function, self.size)
        self._set_storage_volume_from_mass_content(mass_content_total)
        self._set_cushion_gas_volume_from_storage_volume()

    def get_buffer_init(self):
        return self.buffer_init

    def _get_cushion_gas_volume_from_storage_volume(self, volume):
        """
        Function sets the norm volume of the storage. Thats calculated by newton algorithm for real gas pressure calculation
        Returns:

        """

        function = lambda molar_content: self._get_van_der_waals_pressure(molar_content, volume) - self.pressure_min
        molar_content = newton(function, volume * self.pressure_min / 101300)
        mass_content = self._get_mass_content_from_molar(molar_content)
        return self._get_norm_volume(mass_content)

    def _set_cushion_gas_volume_from_storage_volume(self):
        """
        Function sets the norm volume of the storage. Thats calculated by newton algorithm for real gas pressure calculation
        Returns:

        """

        volume = self.storage_volume
        function = lambda molar_content: self._get_van_der_waals_pressure(molar_content, volume) - self.pressure_min
        molar_content = newton(function, volume * self.pressure_min / 101300)
        mass_content = self._get_mass_content_from_molar(molar_content)
        self.cushion_gas_volume = self._get_norm_volume(mass_content)

    def _set_storage_volume_from_cushion_gas_volume(self):
        """
        Function sets the norm volume of the storage. Thats calculated by newton algorithm for real gas pressure calculation
        Returns:

        """

        molar_content = self._get_molar_content_from_norm_volume(self.cushion_gas_volume)
        function = lambda volume: self._get_van_der_waals_pressure(molar_content, volume) - self.pressure_min
        self.storage_volume = newton(function, self.cushion_gas_volume / (self.pressure_min / 101300))

    def _set_van_der_waals(self):
        """
        Calculates the van der waals coefficients to calculate the real gas
        Todo:
            Include the formulas in the documentation from https://ep.liu.se/ecp/157/068/ecp19157068.pdf
        """
        self.van_der_waals_a = 27 * (Constants.gas_constant * self.gas_properties_norm.T_critical()) ** 2 / (
                64 * self.gas_properties_norm.p_critical())
        #  (Nm/(mol*K)*K)^2 / (N/m²) = N/m^2 * (m^3)^2 / mol^2 = Pa * (m^3)^2 / mol^2
        self.van_der_waals_b = Constants.gas_constant * self.gas_properties_norm.T_critical() / (
                8 * self.gas_properties_norm.p_critical())
        #  Nm/(mol*K) * K / (N/m²) = m³ / mol

    def _get_molar_content_from_norm_volume(self, norm_volume):
        """
        Returns the molar content of the gas defined by the norm volume

        Args:
            norm_volume (float): Norm volume of the gas

        Returns:
            float: molar_content of the gas in mol
        """
        return norm_volume * self.gas_properties_norm.rhomolar()

    def _get_molar_content_from_mass(self, mass_content):

        """
        Returns the molar content of the gas defined by the norm volume
        Args:
            mass_content (float): Given Mass in kg

        Returns:
            float: molar_content of the gas mol
        """

        return mass_content / (self.gas_properties_norm.molar_mass())

    def _get_mass_content_from_pressure(self, pressure):
        volume = self.storage_volume
        function = lambda molar_content: self._get_van_der_waals_pressure(molar_content, volume) - pressure
        if self.size is not None:
            start_filling = self.size
        elif self.buffer_init != 0:
            start_filling = self.buffer_init
        elif self.buffer_min is not None:
            start_filling = self.buffer_min
        else:
            start_filling = 50000
        molar_content = newton(function,
                               self._get_molar_content_from_mass(start_filling))
        return self._get_mass_content_from_molar(molar_content)

    def _get_mass_content_from_molar(self, molar_content):
        """
        Returns the mass content from molar content
        Args:
            molar_content (float): Molar gas content in mol

        Returns:
            float: mass_content of the gas in kg
        """

        return molar_content * (self.gas_properties_norm.molar_mass())

    def _get_norm_volume(self, buffer_level: float):
        """
        Returns the norm_volume of the storage at a specific buffer_level
        Args:
            buffer_level (float): Buffer level of the storage in kg

        Returns:
            float: Norm volume of the gas content
        """

        volume = float(buffer_level) / self.gas_properties_norm.rhomass()
        return volume

    def _calculate_gas_pressure(self, buffer_level: float):
        """
        Calculatione method to determine the storage pressure based on the buffer_level of the storage

        Args:
            buffer_level (float): Buffer level of the storage in kg

        Returns:
            float: Pressure of the storage in Pa
        """
        # Calculate pressure based on isothermic change of state
        # Under pressure the gas has the partial volume calculated by _calculate_gas_volume
        # When amount is reduced it has the whole max_gas_volume
        # https://www.chemie.de/lexikon/Van-der-Waals-Gleichung.html

        molar_content = self._get_molar_content_from_mass(buffer_level) + self._get_molar_content_from_norm_volume(
            self.cushion_gas_volume)
        pressure = self._get_van_der_waals_pressure(molar_content, self.storage_volume)

        return pressure

    def _get_van_der_waals_pressure(self, molar_content, volume):
        """
        Returns the pressure of the storage based on the van-der-waals equation using the molar content and the standard volume of the storage
        Args:
            molar_content (float): Molar content that is stored in the storage in mol
            volume (float): Standard volume of the storage in m³

        Returns:
            float: Pressure of the storage in Pa

        """

        pressure = (molar_content * Constants.gas_constant * self.storage_temperature) / \
                   (volume - molar_content * self.van_der_waals_b) - \
                   (self.van_der_waals_a * molar_content ** 2) / \
                   (volume ** 2)
        # = mol * K * Nm / (mol * K) / (m³ - mol * m³ / mol) - (Pa * (m^3)^2 / mol^2) * mol^2) / (m³)^2
        # = Nm / m³  - Pa
        # Pa = Pa - Pa

        return pressure

    def run(self, port_id, branch_information, runcount=0):

        """
        Run method of the gas storage which is called by the branch object while solving

        Args:
            port_id (str): ID of the branch connected port
            branch_information (dict): Information about the branch state at the runcount that includes (pressure, temperature, fraction, stream)
            runcount (int): Runcount of the model for which the component has to be solved

        """
        self.status = 0  # set default status with 0:ok; >0:warning; <0:error
        if not isinstance(self.ports[port_id],Port_Energy):
            mass_fraction = self.ports[port_id].get_mass_fraction()
            if self.mass_fraction != mass_fraction:
                if runcount != 0:
                    logging.critical(f'Mass fraction of storage input changed at runcount {runcount}. '
                                     f'That is not included in calculation of storage')
                # self._update_properties()
                self.mass_fraction = mass_fraction
                # if self.pressure_max != None or self.pressure_min != None:
                #    self.gas_properties_norm = RefPropFluid.create_fluid(mass_fraction, pressure=101325, temperature=273.15)
                #    self.mass_content_min = self._get_mass_content_from_molar(
                #        self._get_molar_content_from_norm_volume(self.cushion_gas_volume))
                #    self._set_van_der_waals()

        # reset buffer if runcount is zero
        if runcount == 0:
            self.buffer_old = 0 if self.buffer_init is None else self.buffer_init
            self.buffer_new = 0 if self.buffer_init is None else self.buffer_init
            self.runcount_old = 0

        # only apply taken action to storage if run count change
        if runcount != self.runcount_old:
            self.runcount_old = runcount
            self.buffer_old = self.buffer_new

        # calculate energy flow
        [controlled_port, energy_stream, loop_control] = self._calc_control_var(port_id, branch_information[
            PhysicalQuantity.stream])
        # set flow by profile no matter if active or not
        if self.active & (not loop_control):
            if self.charge_power > self.energy_to_power(self.size):
                energy_stream = self.size
            else:
                energy_stream = self.power_to_energy(self.charge_power)

        energy_stream = range_limit(energy_stream, -self.power_to_energy(self.charge_power),
                                    self.power_to_energy(self.charge_power))

        # add the flows to the storage
        if energy_stream < 0:
            self.buffer_new = self.buffer_old - energy_stream * self.efficiency
        else:
            self.buffer_new = self.buffer_old - energy_stream / self.efficiency

        # limit flows to the system
        if self.size is not None:
            if self.buffer_new > self.size:
                diff = self.buffer_new - self.size / self.efficiency
                energy_stream += diff
                self.buffer_new = self.size
            else:
                if self.buffer_new < 0:
                    diff = self.buffer_new * self.efficiency
                    energy_stream += diff
                    self.buffer_new = 0

        # calculate pressure of storage
        if self.pressure_max is not None and self.pressure_min is not None and self.storage_volume != 0:
            storage_pressure = self._calculate_gas_pressure(self.buffer_new)
            if storage_pressure < self.pressure_min and abs(storage_pressure - self.pressure_min) > 1e-2:
                logging.warning('Pressure of storage dropped below minimum pressure')
                storage_pressure = self.pressure_min
                min_mass_content = self._get_mass_content_from_pressure(self.pressure_min) - self.buffer_min
                diff = self.buffer_new - min_mass_content
                energy_stream += diff
                self.buffer_new = min_mass_content
            if storage_pressure > self.pressure_max:
                storage_pressure = self.pressure_max
                max_mass_content = self._get_mass_content_from_pressure(self.pressure_max) - self.buffer_min
                diff = self.buffer_new - max_mass_content
                energy_stream += diff
                self.buffer_new = max_mass_content
            # run compression of the input gas
            if Compressor in [component.__class__ for component in
                              self.sub_components.values()] and self.include_compression is True:
                port_id_in_compressor = self.sub_components[str(Compressor.__name__)].mass_ports['in']
                port_electric_compressor = self.sub_components[str(Compressor.__name__)].get_ports_by_type_and_sign(
                    StreamEnergy.ELECTRIC, StreamDirection.stream_into_component) #ELECTRIC PORT OF SUB_COMPONENT COMPRESSOR
                port_electric = self.get_ports_by_type_and_sign(StreamEnergy.ELECTRIC,
                                                                StreamDirection.stream_into_component) #Electric Port STORAGE
                self.sub_components[str(Compressor.__name__)].run(port_id_in_compressor, branch_information, runcount,
                                                                  pressure_out=storage_pressure)
                port_electric.set_all_properties(runcount, port_electric_compressor)

        # Add values to component histories

        if runcount >= len(self.component_technical_results.component_history['storage_level']):
            self.component_technical_results.component_history['storage_level'].append(0)
            self.component_technical_results.component_history[PhysicalQuantity.pressure].append(0)
        if self.pressure_max is not None and self.pressure_min is not None and self.storage_volume != 0:
            self.component_technical_results.component_history[PhysicalQuantity.pressure][runcount] = storage_pressure
        self.component_technical_results.component_history['storage_level'][runcount] = self.buffer_new

        # return output -> discharge storage
        if energy_stream < 0:
            self.mass_ports['out'].set_stream(runcount, 0)
            self.mass_ports['in'].set_stream(runcount, energy_stream)
        else:
            self.mass_ports['in'].set_stream(runcount, 0)
            self.mass_ports['out'].set_stream(runcount, energy_stream)
            self.mass_ports['out'].set_pressure(self.mass_ports['in'].get_pressure())
            self.mass_ports['out'].set_temperature(self.mass_ports['in'].get_temperature())

        if runcount > 0:
            if energy_stream < 0:
                if abs(self.component_technical_results.component_history['storage_level'][runcount] - self.component_technical_results.component_history['storage_level'][
                    runcount - 1] + energy_stream * self.efficiency) > 1e-2:
                    val =abs(self.component_technical_results.component_history['storage_level'][runcount] -
                             self.component_technical_results.component_history['storage_level'][
                                    runcount - 1] + energy_stream * self.efficiency)
                    logging.warning(
                        f'The difference between buffer level change and charge/discharge energy is {val} \n '
                        f'At Timestep {runcount}')
                    self.status = 1
            else:
                if abs(self.component_technical_results.component_history['storage_level'][runcount] - self.component_technical_results.component_history['storage_level'][
                    runcount - 1] + energy_stream / self.efficiency) > 1e-2:
                    val = abs(self.component_technical_results.component_history['storage_level'][runcount] -
                              self.component_technical_results.component_history['storage_level'][
                                    runcount - 1] + energy_stream / self.efficiency)
                    logging.warning(
                        f'The difference between buffer level change and charge/discharge energy is {val} \n At Timestep {runcount}')
                    self.status = 1